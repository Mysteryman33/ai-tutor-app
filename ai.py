import os
import requests
from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    current_user, logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---------------- MODELS ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    role = db.Column(db.String(10))
    content = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- GROQ ----------------
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

NORMAL_PROMPT = "You are an AI assistant that explains clearly."
TUTOR_PROMPT = "You are a tutor. Never give final answers."

def ask_ai(prompt, mode, history):
    system_prompt = TUTOR_PROMPT if mode == "tutor" else NORMAL_PROMPT
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
    }

    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        data = r.json()

        if "choices" not in data:
            if "error" in data:
                return f"⚠️ AI Error: {data['error'].get('message', 'Unknown error')}"
            return "⚠️ Unexpected AI response."

        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Server Error: {str(e)}"

# ---------------- BASE UI ----------------

BASE_CSS = """
<style>
* { box-sizing:border-box; }
body {
  margin:0;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:radial-gradient(circle at top,#1e1b4b 0,#0f172a 40%,#020617 100%);
  color:#e5e7eb;
}
a { text-decoration:none; }

/* NAVBAR */
.nav {
  position:fixed;
  top:0; left:0; right:0;
  height:60px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 32px;
  background:rgba(15,23,42,0.9);
  backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(148,163,184,0.25);
  z-index:20;
}
.nav-left { display:flex; align-items:center; gap:10px; }
.nav-logo {
  width:32px; height:32px;
  border-radius:999px;
  background:conic-gradient(from 180deg,#38bdf8,#6366f1,#a855f7,#ec4899,#38bdf8);
  display:flex; align-items:center; justify-content:center;
  color:#0b1120; font-weight:700; font-size:16px;
}
.nav-title { font-weight:600; letter-spacing:0.03em; font-size:15px; }
.nav-links a {
  color:#e5e7eb;
  font-size:14px;
  margin-left:18px;
  padding:6px 14px;
  border-radius:999px;
}
.nav-links a:hover { background:rgba(148,163,184,0.2); }

/* PAGE LAYOUT */
.page {
  min-height:100vh;
  padding-top:80px;
  display:flex;
  align-items:center;
  justify-content:center;
  padding-bottom:40px;
}

/* AUTH CARDS */
.glass-card {
  width:100%;
  max-width:420px;
  padding:38px 34px 32px;
  border-radius:28px;
  background:rgba(15,23,42,0.55);
  backdrop-filter:blur(22px);
  border:1px solid rgba(148,163,184,0.25);
  box-shadow:0 26px 90px rgba(0,0,0,0.65);
}
.glass-card h1 {
  margin:0 0 6px;
  font-size:28px;
  font-weight:600;
}
.glass-sub {
  font-size:14px;
  color:#9ca3af;
  margin-bottom:22px;
}

/* INPUTS */
label {
  font-size:13px;
  color:#9ca3af;
}
input {
  width:100%;
  margin-top:6px;
  margin-bottom:16px;
  padding:13px 16px;
  border-radius:999px;
  border:1px solid rgba(55,65,81,0.9);
  background:rgba(15,23,42,0.95);
  color:#e5e7eb;
  font-size:15px;
}
input::placeholder { color:#6b7280; }
input:focus {
  outline:none;
  border-color:#6366f1;
  box-shadow:0 0 0 2px rgba(99,102,241,0.45);
}

/* BUTTONS */
.btn {
  width:100%;
  padding:13px 0;
  border-radius:999px;
  border:none;
  font-size:15px;
  cursor:pointer;
  margin-top:6px;
}
.btn-primary {
  background:linear-gradient(135deg,#6366f1,#4f46e5);
  color:white;
}
.btn-secondary {
  background:rgba(15,23,42,0.9);
  color:#e5e7eb;
  border:1px solid rgba(148,163,184,0.4);
}
.btn-primary:hover { filter:brightness(1.05); }
.btn-secondary:hover { background:rgba(15,23,42,1); }

/* ERROR BOX */
.error {
  background:rgba(248,113,113,0.12);
  border:1px solid rgba(248,113,113,0.6);
  color:#fecaca;
  padding:10px 12px;
  border-radius:12px;
  font-size:13px;
  margin-bottom:14px;
}

/* CHAT UI */
.chat-shell {
  width:100%;
  max-width:1100px;
  height:80vh;
  border-radius:28px;
  background:radial-gradient(circle at top,#111827 0,#020617 55%,#020617 100%);
  border:1px solid rgba(148,163,184,0.35);
  box-shadow:0 30px 90px rgba(15,23,42,0.95);
  display:flex;
  overflow:hidden;
}
.chat-sidebar {
  width:260px;
  border-right:1px solid rgba(31,41,55,0.9);
  padding:18px 16px;
}
.chat-sidebar h3 {
  margin:0 0 6px;
  font-size:15px;
}
.chat-sidebar p {
  margin:0 0 14px;
  font-size:12px;
  color:#9ca3af;
}
.chat-sidebar .pill {
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:6px 10px;
  border-radius:999px;
  background:rgba(15,23,42,1);
  border:1px solid rgba(55,65,81,0.9);
  font-size:11px;
  color:#9ca3af;
}
.chat-main {
  flex:1;
  display:flex;
  flex-direction:column;
  padding:14px 16px;
}
.chat-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding-bottom:10px;
  border-bottom:1px solid rgba(31,41,55,0.9);
}
.chat-header-left {
  display:flex;
  flex-direction:column;
}
.chat-header-left span:first-child {
  font-size:14px;
  font-weight:500;
}
.chat-header-left span:last-child {
  font-size:11px;
  color:#9ca3af;
}
.chat-header-right select {
  background:#020617;
  color:#e5e7eb;
  border-radius:999px;
  border:1px solid rgba(75,85,99,0.9);
  padding:6px 10px;
  font-size:12px;
}

/* Messages */
.chat-window {
  flex:1;
  overflow-y:auto;
  padding:12px 4px;
  margin-top:6px;
}
.msg {
  display:flex;
  margin-bottom:10px;
}
.msg.user { justify-content:flex-end; }
.msg.assistant { justify-content:flex-start; }
.bubble {
  max-width:70%;
  padding:10px 14px;
  border-radius:18px;
  font-size:14px;
  line-height:1.4;
}
.msg.user .bubble {
  background:linear-gradient(135deg,#6366f1,#4f46e5);
  color:white;
  border-bottom-right-radius:4px;
}
.msg.assistant .bubble {
  background:#020617;
  border:1px solid rgba(55,65,81,0.9);
  color:#e5e7eb;
  border-bottom-left-radius:4px;
}

/* Input bar */
.chat-input-row {
  margin-top:8px;
  padding-top:8px;
  border-top:1px solid rgba(31,41,55,0.9);
  display:flex;
  gap:8px;
}
.chat-input-row input {
  flex:1;
  background:#020617;
  border-radius:999px;
  border:1px solid rgba(55,65,81,0.9);
  color:#e5e7eb;
  padding:10px 14px;
  font-size:14px;
}
.chat-input-row button {
  border-radius:999px;
  border:none;
  padding:0 18px;
  background:linear-gradient(135deg,#6366f1,#4f46e5);
  color:white;
  font-size:14px;
  cursor:pointer;
}
.chat-input-row button:hover { filter:brightness(1.05); }

/* SIMPLE CARDS */
.simple-card {
  width:100%;
  max-width:700px;
  padding:24px 22px;
  border-radius:24px;
  background:linear-gradient(135deg,rgba(15,23,42,0.95),rgba(15,23,42,0.8));
  border:1px solid rgba(148,163,184,0.35);
  box-shadow:0 24px 80px rgba(15,23,42,0.9);
}
.simple-card h2 { margin-top:0; margin-bottom:10px; }
.simple-card p { font-size:13px; color:#9ca3af; }
.history-item {
  padding:8px 10px;
  border-radius:12px;
  margin-bottom:6px;
  font-size:13px;
}
.history-item.user { background:rgba(37,99,235,0.15); }
.history-item.assistant { background:rgba(15,23,42,0.9); }
.history-item b { margin-right:6px; }
</style>
"""

NAVBAR = """
<div class="nav">
  <div class="nav-left">
    <div class="nav-logo">A</div>
    <div class="nav-title">AceTutor</div>
  </div>
  <div class="nav-links">
    {% if current_user.is_authenticated %}
      <a href="/dashboard">Home</a>
      <a href="/chat">Chat</a>
      <a href="/history">History</a>
      <a href="/profile">Profile</a>
      <a href="/settings">Settings</a>
      <a href="/logout">Logout</a>
    {% else %}
      <a href="/">Home</a>
      <a href="/login">Login</a>
      <a href="/register">Register</a>
    {% endif %}
  </div>
</div>
"""

# ---------------- ROUTES ----------------

@app.route("/")
def landing():
    return render_template_string(
        BASE_CSS + NAVBAR + """
<div class="page">
  <div class="glass-card">
    <h1>Welcome to AceTutor</h1>
    <p class="glass-sub">Your AI tutor for homework, studying, and learning anything.</p>
    <a href="/login"><button class="btn btn-primary">Login</button></a>
    <a href="/register"><button class="btn btn-secondary">Register</button></a>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            login_user(user)
            return redirect("/dashboard")
        error = "Invalid username or password."

    return render_template_string(
        BASE_CSS + NAVBAR + f"""
<div class="page">
  <div class="glass-card">
    <h1>Sign in</h1>
    <p class="glass-sub">Welcome back! Let's continue learning.</p>
    {"<div class='error'>" + error + "</div>" if error else ""}
    <form method="POST">
      <label>Username</label>
      <input name="username" placeholder="Enter your username">
      <label>Password</label>
      <input name="password" type="password" placeholder="Enter your password">
      <button class="btn btn-primary" type="submit">Login</button>
    </form>
    <p class="glass-sub" style="margin-top:10px;">No account? <a href="/register" style="color:#93c5fd;">Register</a></p>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if User.query.filter_by(username=u).first():
            error = "Username already taken."
        else:
            user = User(username=u, password=generate_password_hash(p))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect("/dashboard")

    return render_template_string(
        BASE_CSS + NAVBAR + f"""
<div class="page">
  <div class="glass-card">
    <h1>Create account</h1>
    <p class="glass-sub">Join AceTutor and start learning smarter.</p>
    {"<div class='error'>" + error + "</div>" if error else ""}
    <form method="POST">
      <label>Username</label>
      <input name="username" placeholder="Choose a username">
      <label>Password</label>
      <input name="password" type="password" placeholder="Choose a password">
      <button class="btn btn-primary" type="submit">Register</button>
    </form>
    <p class="glass-sub" style="margin-top:10px;">Already have an account? <a href="/login" style="color:#93c5fd;">Login</a></p>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template_string(
        BASE_CSS + NAVBAR + f"""
<div class="page">
  <div class="glass-card">
    <h1>Hi, {current_user.username} 👋</h1>
    <p class="glass-sub">Ready to learn something new today?</p>
    <a href="/chat"><button class="btn btn-primary">Open Chat</button></a>
    <a href="/history"><button class="btn btn-secondary">View History</button></a>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/chat")
@login_required
def chat():
    return render_template_string(
        BASE_CSS + NAVBAR + """
<div class="page">
  <div class="chat-shell">
    <div class="chat-sidebar">
      <h3>Session</h3>
      <p>Chat with your tutor, ask questions, and explore ideas.</p>
      <div class="pill">
        <span>Mode:</span>
        <span id="mode-label">Normal</span>
      </div>
    </div>
    <div class="chat-main">
      <div class="chat-header">
        <div class="chat-header-left">
          <span>AceTutor Chat</span>
          <span>Ask anything. Get step-by-step help.</span>
        </div>
        <div class="chat-header-right">
          <select id="mode-select" onchange="document.getElementById('mode-label').innerText=this.value==='tutor'?'Tutor':'Normal';">
            <option value="normal">Normal</option>
            <option value="tutor">Tutor</option>
          </select>
        </div>
      </div>
      <div id="chat-window" class="chat-window">
        <div class="msg assistant">
          <div class="bubble">Hey! I’m your AceTutor. What are we working on today?</div>
        </div>
      </div>
      <div class="chat-input-row">
        <input id="chat-input" placeholder="Type your question or prompt..." autocomplete="off">
        <button id="send-btn">Send</button>
      </div>
    </div>
  </div>
</div>

<script>
const chatWindow = document.getElementById("chat-window");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const modeSelect = document.getElementById("mode-select");

function appendMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = "msg " + role;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  appendMessage("user", text);
  input.value = "";

  const mode = modeSelect.value;

  const loading = document.createElement("div");
  loading.className = "msg assistant";
  const lb = document.createElement("div");
  lb.className = "bubble";
  lb.textContent = "Thinking...";
  loading.appendChild(lb);
  chatWindow.appendChild(loading);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  try {
    const res = await fetch("/chat_api", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:text, mode:mode})
    });
    const data = await res.json();
    chatWindow.removeChild(loading);
    appendMessage("assistant", data.reply);
  } catch(e) {
    chatWindow.removeChild(loading);
    appendMessage("assistant", "Error talking to server.");
  }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});
</script>
""",
        current_user=current_user,
    )

@app.route("/chat_api", methods=["POST"])
@login_required
def chat_api():
    data = request.get_json()
    msg = data.get("message", "")
    mode = data.get("mode", "normal")

    history = [
        {"role": c.role, "content": c.content}
        for c in Chat.query.filter_by(user_id=current_user.id)
    ]

    reply = ask_ai(msg, mode, history)

    db.session.add(Chat(user_id=current_user.id, role="user", content=msg))
    db.session.add(Chat(user_id=current_user.id, role="assistant", content=reply))
    db.session.commit()

    return {"reply": reply}

@app.route("/history")
@login_required
def history():
    chats = Chat.query.filter_by(user_id=current_user.id).all()
    items = ""
    for c in chats:
        items += f"<div class='history-item {c.role}'><b>{c.role}:</b>{c.content}</div>"
    if not items:
        items = "<p>No history yet. Start a chat first.</p>"
    return render_template_string(
        BASE_CSS + NAVBAR + f"""
<div class="page">
  <div class="simple-card">
    <h2>Chat history</h2>
    <p>Review everything you and AceTutor have discussed.</p>
    <div style="margin-top:12px; max-height:55vh; overflow-y:auto;">
      {items}
    </div>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/profile")
@login_required
def profile():
    return render_template_string(
        BASE_CSS + NAVBAR + f"""
<div class="page">
  <div class="simple-card">
    <h2>Profile</h2>
    <p>Basic account details.</p>
    <p style="margin-top:12px;"><b>Username:</b> {current_user.username}</p>
  </div>
</div>
""",
        current_user=current_user,
    )

@app.route("/settings")
@login_required
def settings():
    return render_template_string(
        BASE_CSS + NAVBAR + """
<div class="page">
  <div class="simple-card">
    <h2>Settings</h2>
    <p>Future options like themes, preferences, and more can live here.</p>
  </div>
</div>
""",
        current_user=current_user,
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

