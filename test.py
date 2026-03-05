import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HF_API_KEY = HF_API_KEY = os.getenv("HF_API_KEY")
MODEL = "meta-llama/Llama-3.2-1B-Instruct"

NORMAL_STYLES = {
    "friendly": "You respond warmly, casually, and with humor.",
    "professional": "You respond formally and concisely.",
    "sarcastic": "You use dry humor and light sarcasm.",
    "storyteller": "You speak dramatically, like a fantasy narrator."
}

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

    system_prompt = (
        TUTOR_STYLES.get(style, "You are a tutor who gives hints, not answers.")
        if mode == "tutor"
        else NORMAL_STYLES.get(style, "You respond normally.")
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        raw = r.text
        print("RAW RESPONSE:", raw)

        # Try to parse JSON
        try:
            data = r.json()
        except:
            return f"Error: API returned non‑JSON response: {raw}"

        # If API returned a string instead of a dict
        if isinstance(data, str):
            return f"API returned a string instead of JSON: {data}"

        # If API returned an error object
        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            if isinstance(err, dict):
                return f"API Error: {err.get('message', 'Unknown error')}"
            else:
                return f"API Error: {err}"

        # If API returned the expected structure
        if isinstance(data, dict) and "choices" in data:
            try:
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Error: Unexpected model response format: {data}"

        # Anything else
        return f"Unexpected API response: {data}"

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
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: "Inter", Arial, sans-serif;
            background: linear-gradient(135deg, #6a11cb, #2575fc);
            background-size: 300% 300%;
            animation: gradientShift 12s ease infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .chat-container {
            width: 450px;
            height: 720px;
            backdrop-filter: blur(22px) saturate(180%);
            -webkit-backdrop-filter: blur(22px) saturate(180%);
            background: rgba(255, 255, 255, 0.18);
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            box-shadow: 0 8px 40px rgba(0,0,0,0.25);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            padding: 20px;
            text-align: center;
            font-size: 22px;
            font-weight: 600;
            color: white;
            letter-spacing: 0.5px;
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(18px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.25);
        }

        .settings {
            padding: 14px;
            backdrop-filter: blur(18px);
            background: rgba(255, 255, 255, 0.10);
            border-bottom: 1px solid rgba(255, 255, 255, 0.25);
        }

        .settings label {
            font-size: 14px;
            font-weight: 600;
            color: white;
        }

        .settings select {
            width: 100%;
            margin-top: 6px;
            margin-bottom: 12px;
            padding: 10px;
            border-radius: 12px;
            border: none;
            background: rgba(255, 255, 255, 0.25);
            color: white;
            backdrop-filter: blur(12px);
            font-size: 14px;
            outline: none;
        }

        #chat {
            flex: 1;
            padding: 18px;
            overflow-y: auto;
        }

        .msg {
            margin: 12px 0;
            padding: 14px 18px;
            border-radius: 16px;
            max-width: 80%;
            line-height: 1.45;
            font-size: 15px;
            backdrop-filter: blur(14px);
            background: rgba(255, 255, 255, 0.25);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.35);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: fadeIn 0.25s ease-out;
        }

        .user {
            align-self: flex-end;
            background: rgba(80, 160, 255, 0.35);
        }

        .ai {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.25);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .input-area {
            display: flex;
            padding: 14px;
            backdrop-filter: blur(18px);
            background: rgba(255, 255, 255, 0.12);
            border-top: 1px solid rgba(255, 255, 255, 0.25);
        }

        #msg {
            flex: 1;
            padding: 12px 14px;
            border-radius: 14px;
            border: none;
            outline: none;
            font-size: 15px;
            background: rgba(255, 255, 255, 0.25);
            color: white;
            backdrop-filter: blur(12px);
        }

        #msg::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        #send {
            margin-left: 10px;
            padding: 0 22px;
            border-radius: 14px;
            border: none;
            cursor: pointer;
            font-size: 15px;
            background: rgba(255, 255, 255, 0.35);
            color: #1a1a1a;
            backdrop-filter: blur(12px);
            transition: 0.2s;
        }

        #send:hover {
            background: rgba(255, 255, 255, 0.55);
        }
    </style>
</head>
<body>

    <div class="chat-container">
        <div class="header">AI Tutor</div>

        <div class="settings">
            <label>Mode:</label>
            <select id="mode">
                <option value="normal">Normal</option>
                <option value="tutor">Tutor (Hints Only)</option>
            </select>

            <label>Style:</label>
            <select id="style">
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)







