import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load API key from environment (Render/Railway/Replit)
HF_API_KEY = "https://ai-tutor-app-2.onrender.com"
MODEL = "meta-llama/Llama-3.2-1B-Instruct"

# Normal mode styles
NORMAL_STYLES = {
    "friendly": "You respond warmly, casually, and with humor.",
    "professional": "You respond formally and concisely.",
    "sarcastic": "You use dry humor and light sarcasm.",
    "storyteller": "You speak dramatically, like a fantasy narrator."
}

# Tutor mode styles (no direct answers)
TUTOR_STYLES = {
    "friendly": "You are a friendly tutor. You never give the full answer. You give hints, guiding questions, and small steps to help the student think for themselves.",
    "professional": "You are a clear and structured instructor. You avoid giving direct answers. You explain concepts, give partial steps, and help the student reason through the problem.",
    "sarcastic": "You use light, school‑appropriate sarcasm, but you still avoid giving answers. You give hints and nudges instead of solutions.",
    "storyteller": "You explain ideas like a storyteller or narrator, but you never reveal the full answer. You guide the student with clues and thought‑provoking steps."
}


def ask_ai(prompt, style, mode):
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    # Choose correct style set
    if mode == "tutor":
        system_prompt = TUTOR_STYLES.get(style, "You are a tutor who gives hints, not answers.")
    else:
        system_prompt = NORMAL_STYLES.get(style, "You respond normally.")

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

        if "error" in data:
            return "API Error: " + data["error"]["message"]

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error: {e}"


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Tutor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f2f2f7;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .chat-container {
                width: 420px;
                height: 650px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .header {
                background: #4a6cf7;
                color: white;
                padding: 16px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
            }
            #chat {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
            }
            .msg {
                margin: 10px 0;
                padding: 10px 14px;
                border-radius: 12px;
                max-width: 80%;
                line-height: 1.4;
            }
            .user { background: #d1e7ff; align-self: flex-end; }
            .ai { background: #e9e9eb; align-self: flex-start; }
            .input-area {
                display: flex;
                border-top: 1px solid #ddd;
            }
            #msg {
                flex: 1;
                padding: 14px;
                border: none;
                outline: none;
                font-size: 16px;
            }
            #send {
                background: #4a6cf7;
                color: white;
                border: none;
                padding: 0 20px;
                cursor: pointer;
                font-size: 16px;
            }
            #send:hover { background: #3b57d6; }
        </style>
    </head>
    <body>

        <div class="chat-container">
            <div class="header">AI Tutor</div>

            <div style="padding: 10px; border-bottom: 1px solid #ddd;">
                <label>Mode:</label>
                <select id="mode" style="padding: 6px; width: 100%; margin-top: 6px;">
                    <option value="normal">Normal</option>
                    <option value="tutor">Tutor (Hints Only)</option>
                </select>

                <label style="margin-top: 10px;">Style:</label>
                <select id="style" style="padding: 6px; width: 100%; margin-top: 6px;">
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="sarcastic">Sarcastic</option>
                    <option value="storyteller">Storyteller</option>
                </select>
            </div>

            <div id="chat"></div>

            <div class="input-area">
                <input id="msg" placeholder="Type your message...">
                <button id="send">Send</button>
            </div>
        </div>

        <script>
            const chat = document.getElementById("chat");
            const msg = document.getElementById("msg");
            const send = document.getElementById("send");
            const style = document.getElementById("style");
            const mode = document.getElementById("mode");

            function addMessage(text, sender) {
                const div = document.createElement("div");
                div.className = "msg " + sender;
                div.innerText = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            send.onclick = async () => {
                const text = msg.value.trim();
                if (!text) return;

                addMessage(text, "user");
                msg.value = "";

                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        message: text,
                        style: style.value,
                        mode: mode.value
                    })
                });

                const data = await response.json();
                addMessage(data.reply, "ai");
            };
        </script>

    </body>
    </html>
    """


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    style = request.json.get("style", "friendly")
    mode = request.json.get("mode", "normal")
    reply = ask_ai(user_msg, style, mode)
    return jsonify({"reply": reply})


# Required for Render/Railway hosting
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


