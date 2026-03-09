import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HF_API_KEY = os.getenv("HF_API_KEY")
MODEL = "meta-llama/Llama-3.2-1B-Instruct"

# --- SYSTEM PROMPTS ---
NORMAL_PROMPT = (
    """You are an AI assistant designed to help students understand concepts and solve problems clearly and efficiently. In Normal Mode, your goal is to provide both the reasoning and the final result so the student fully understands how the solution is reached.

Follow these rules:

Always provide the final answer or result when solving a problem. The result should be clearly stated so the student can easily identify it.

Explain the reasoning or steps used to reach the result so the student understands the process behind the solution.

Break complex problems into clear step-by-step explanations when appropriate.

Use clear, simple language appropriate for a student learning the topic.

When helpful, explain relevant concepts, formulas, or strategies that apply to the problem.

If the student makes a mistake, politely explain why it is incorrect and demonstrate the correct reasoning that leads to the final result.

Make sure the response includes both the explanation and the final answer, so
the student can learn the method and see the correct outcome.

Keep explanations organized, accurate, and focused on helping the student understand the topic.
always answer short and simple but enough to help unless they request otherwise"""
)

TUTOR_PROMPT = (
    """You are an AI tutor designed to help students learn by guiding them through problems without directly giving the final answer. Your goal is to help the student develop problem-solving skills rather than simply providing solutions.

Follow these rules strictly:

Never reveal the final answer to any problem, even if the student asks directly for it.

Break the problem into clear steps and guide the student through the reasoning process required to reach the solution themselves.

Ask guiding questions that help the student think about the next step instead of solving it for them.

When appropriate, explain relevant concepts, formulas, or strategies that the student may need.

If the student makes a mistake, politely point out the error and explain why, then guide them toward correcting it.

Encourage the student to attempt each step before moving on.

Provide hints that gradually increase in detail, but stop before revealing the final answer.

always answer short and simple but enough to help unless they request otherwise

NEVER GIVE THE FULL ANSWER

NEVER GIVE THE FULL ASNWER"""
)

# --- AI CALL ---
def ask_ai(prompt, mode):
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = TUTOR_PROMPT if mode == "tutor" else NORMAL_PROMPT

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return "Unexpected API response."

    except Exception as e:
        return f"Error: {e}"


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
<html>
<head>
    <title>ACE Tutor</title>

    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">

    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">

    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
        }

        body {
            font-family: "Inter", Arial, sans-serif;

            background: radial-gradient(circle at 20% 20%, #ffffff2a, #000000aa),
                        linear-gradient(135deg, #4a12b8, #2a4fe0, #ff4eb8);
            background-size: 300% 300%;
            animation: gradientShift 16s ease infinite;

            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            overflow: hidden;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .chat-container {
            width: 80%;
            max-width: 900px;
            height: 65vh;

            display: flex;
            flex-direction: column;

            backdrop-filter: blur(40px) saturate(200%);
            background: rgba(255, 255, 255, 0.12);
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.32);

            box-shadow:
                0 0 45px rgba(255, 255, 255, 0.18),
                inset 0 0 30px rgba(255, 255, 255, 0.12);

            overflow: hidden;
            margin-top: 40px;
        }

        .header {
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;

            font-size: 26px;
            font-weight: 700;
            color: white;
            background: rgba(255, 255, 255, 0.10);
            border-bottom: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 28px 28px 0 0;
            position: relative;
        }

        .header-title {
            pointer-events: none;
        }

        #menuBtn {
            position: absolute;
            right: 18px;
            top: 50%;
            transform: translateY(-50%);
            background: transparent;
            border: none;
            cursor: pointer;
            display: none;
        }

        #menuBtn svg {
            width: 22px;
            height: 22px;
            stroke: white;
        }

        .settings {
            padding: 16px 20px;
            background: rgba(255, 255, 255, 0.07);
            border-bottom: 1px solid rgba(255, 255, 255, 0.22);
            display: flex;
            gap: 30px;
            justify-content: center;
        }

        .settings-group {
            display: flex;
            flex-direction: column;
            width: 200px;
        }

        .settings label {
            font-size: 16px;
            font-weight: 600;
            color: white;
            margin-bottom: 6px;
        }

        .settings select {
            appearance: none;
            padding: 14px 40px 14px 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            background-color: rgba(255, 255, 255, 0.22);
            color: white;
            font-size: 16px;
            cursor: pointer;
            backdrop-filter: blur(18px);
            background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='18' viewBox='0 0 24 24' width='18' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 18px;
        }

        #chat {
            flex: 1;
            padding: 24px 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .intro-text {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 42px;
            color: white;
            opacity: 0;
            animation: fadeInIntro 0.8s ease forwards;
        }

        @keyframes fadeInIntro {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg {
            padding: 16px 20px;
            border-radius: 18px;
            max-width: 70%;
            font-size: 17px;
            color: white;

            background: rgba(255, 255, 255, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.40);
            backdrop-filter: blur(25px);
        }

        .msg.user {
            align-self: flex-end;
            background: rgba(120, 180, 255, 0.38);
        }

        .timestamp {
            font-size: 12px;
            opacity: 0.75;
            margin-top: 10px;
        }

        .input-area {
            width: 80%;
            max-width: 900px;
            margin-top: 40px;
            display: flex;
            justify-content: center;
        }

        .input-wrapper {
            display: flex;
            width: 100%;
            max-width: 650px;
            gap: 12px;
        }

        #msg {
            flex: 1;
            padding: 16px;
            border-radius: 14px;
            border: none;
            background: rgba(255, 255, 255, 0.22);
            color: white !important;
            font-size: 16px;
            backdrop-filter: blur(20px);
        }

        #msg::placeholder {
            color: white !important;
        }

        #send {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: none;
            background: rgba(255, 255, 255, 0.30);
            cursor: pointer;
            backdrop-filter: blur(20px);

            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease, background 0.25s ease;

            display: flex;
            align-items: center;
            justify-content: center;
        }

        #send svg {
            width: 22px;
            height: 22px;
        }

        #send:hover {
            background: rgba(255, 255, 255, 0.45);
        }

        .disclaimer {
            margin-top: 6px;
            color: rgba(255, 255, 255, 0.75);
            font-size: 13px;
        }

        #sheetOverlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.45);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
            z-index: 20;
        }

        #settingsSheet {
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            height: 40%;
            max-height: 320px;
            background: rgba(20, 20, 30, 0.96);
            backdrop-filter: blur(24px);
            border-radius: 18px 18px 0 0;
            padding: 16px 18px 20px;
            box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.6);
            transition: transform 0.25s ease;
            transform: translateY(100%);
            z-index: 30;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        #settingsSheet.active {
            transform: translateY(0);
        }

        #sheetOverlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .sheet-handle {
            width: 40px;
            height: 4px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.35);
            margin: 0 auto 10px;
        }

        .sheet-title {
            color: white;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .sheet-row {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .sheet-row label {
            color: rgba(255, 255, 255, 0.85);
            font-size: 14px;
        }

        .sheet-row select {
            appearance: none;
            padding: 12px 36px 12px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            background-color: rgba(255, 255, 255, 0.16);
            color: white;
            font-size: 16px;
            backdrop-filter: blur(18px);
            background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
            background-repeat: no-repeat;
            background-position: right 10px center;
            background-size: 16px;
        }

        .sheet-close {
            margin-top: auto;
            align-self: flex-end;
            padding: 8px 14px;
            border-radius: 999px;
            border: none;
            background: rgba(255, 255, 255, 0.18);
            color: white;
            font-size: 14px;
            cursor: pointer;
        }

        @media (max-width: 600px) {

            body {
                overflow: auto;
            }

            .chat-container {
                width: 100%;
                max-width: 100%;
                height: calc(100vh - 80px);
                margin-top: 0;
                border-radius: 0;
                background: transparent;
                box-shadow: none;
            }

            .header {
                font-size: 16px;
                padding: 10px 12px;
                justify-content: center;
                border-radius: 0;
                background: transparent;
                border-bottom: none;
            }

            #menuBtn {
                display: block;
            }

            .settings {
                display: none;
            }

            #chat {
                padding: 12px 14px 90px;
                gap: 12px;
                background: transparent;
            }

            .msg {
                max-width: 88%;
                font-size: 16px;
                padding: 12px 14px;
            }

            .input-area {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                width: 100%;
                padding: 10px 10px 16px;
                background: transparent;
                z-index: 25;
            }

            #msg {
                border-radius: 999px;
                padding: 14px 16px;
                background: rgba(0, 0, 0, 0.35);
            }

            #send {
                width: 46px;
                height: 46px;
                background: rgba(255, 255, 255, 0.30);
            }
        }
    </style>
</head>

<body>

    <div class="chat-container">
        <div class="header">
            <div class="header-title">ACE Tutor</div>
            <button id="menuBtn" aria-label="Settings">
                <svg viewBox="0 0 24 24" fill="none">
                    <circle cx="5" cy="12" r="1.6" fill="white"/>
                    <circle cx="12" cy="12" r="1.6" fill="white"/>
                    <circle cx="19" cy="12" r="1.6" fill="white"/>
                </svg>
            </button>
        </div>

        <div class="settings">
            <div class="settings-group">
                <label>Mode:</label>
                <select id="mode">
                    <option value="normal">Normal</option>
                    <option value="tutor">Tutor (Hints Only)</option>
                </select>
            </div>
        </div>

        <div id="chat">
            <div class="intro-text">Hey, what can I help with today?</div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrapper">
            <input id="msg" placeholder="Type your message...">

            <button id="send">
                <svg viewBox="0 0 24 24" fill="none">
                    <path d="M5 12h14M12 5l7 7-7 7" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        </div>
    </div>

    <div class="disclaimer">ACE Tutor can make mistakes. Check important info.</div>

    <div id="sheetOverlay"></div>

    <div id="settingsSheet">
        <div class="sheet-handle"></div>
        <div class="sheet-title">Settings</div>

        <div class="sheet-row">
            <label for="modeSheet">Mode</label>
            <select id="modeSheet">
                <option value="normal">Normal</option>
                <option value="tutor">Tutor (Hints Only)</option>
            </select>
        </div>

        <button class="sheet-close" id="sheetClose">Close</button>
    </div>

    <script>
        const chat = document.getElementById("chat");
        const msg = document.getElementById("msg");
        const send = document.getElementById("send");
        const mode = document.getElementById("mode");

        const modeSheet = document.getElementById("modeSheet");
        const menuBtn = document.getElementById("menuBtn");
        const sheetOverlay = document.getElementById("sheetOverlay");
        const settingsSheet = document.getElementById("settingsSheet");
        const sheetClose = document.getElementById("sheetClose");

        function timestamp() {
            const d = new Date();
            return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        }

        function addMessage(text, sender) {
            const div = document.createElement("div");
            div.className = "msg " + sender;

            const content = document.createElement("div");
            content.innerHTML = text;

            const time = document.createElement("div");
            time.className = "timestamp";
            time.innerText = timestamp();

            div.appendChild(content);
            div.appendChild(time);

            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function sendMessage() {
            const text = msg.value.trim();
            if (!text) return;

            addMessage(text, "user");
            msg.value = "";

            send.style.opacity = "0";
            send.style.pointerEvents = "none";

            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    message: text,
                    mode: mode.value
                })
            });

            const data = await response.json();
            addMessage(data.reply, "ai");
        }

        send.onclick = sendMessage;

        msg.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });

msg.addEventListener("input", () => {
    if (msg.value.trim().length > 0) {
        send.style.opacity = "1";
        send.style.pointerEvents = "auto";
    } else {
        send.style.opacity = "0";
        send.style.pointerEvents = "none";
    }
});

/* sync sheet selects with main selects */
function syncSheetFromMain() {
    modeSheet.value = mode.value;
}

function syncMainFromSheet() {
    mode.value = modeSheet.value;
}

modeSheet.addEventListener("change", syncMainFromSheet);

/* bottom sheet open/close */
function openSheet() {
    syncSheetFromMain();
    sheetOverlay.classList.add("active");
    settingsSheet.classList.add("active");
}

function closeSheet() {
    sheetOverlay.classList.remove("active");
    settingsSheet.classList.remove("active");
}

menuBtn.addEventListener("click", openSheet);
sheetClose.addEventListener("click", closeSheet);
sheetOverlay.addEventListener("click", closeSheet);
    </script>

</body>
</html>
    """


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    mode = request.json.get("mode", "normal")
    reply = ask_ai(user_msg, mode)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
