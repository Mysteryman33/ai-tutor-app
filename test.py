import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HF_API_KEY = HF_API_KEY = os.getenv("HF_API_KEY")
MODEL = "meta-llama/Llama-3.2-1B-Instruct"

NORMAL_STYLES = {
    "friendly": "In this mode and style, respond in a warm, supportive, and conversational tone. You may give the final answer and explain it clearly, but do so in a way that feels approachable and encouraging. Use simple language when possible and make the user feel comfortable asking questions. Be positive, motivating, and helpful while still ensuring the explanation is accurate and useful.",
    "professional": "In this mode and style, respond with a clear, structured, and academic tone. Provide direct answers along with concise explanations when appropriate. Focus on accuracy, logic, and clarity, similar to a knowledgeable teacher or expert explaining a concept. Avoid slang, jokes, or overly casual language. Organize explanations logically and keep responses professional, informative, and easy to understand.",
    "storyteller": "In this mode and style, you may provide the final answer but explain concepts through engaging narratives, analogies, or imaginative scenarios. Present information in a way that feels like a short story or vivid explanation that helps the user visualize the concept. The response should still be educational and accurate, but the tone should feel engaging, descriptive, and memorable."
}

TUTOR_STYLES = {
    "friendly": "You are a friendly tutor. You never give the full answer. You give hints, guiding questions, and small steps to help the student think for themselves.",
    "professional": "You are a clear and structured instructor. You avoid giving direct answers. You explain concepts, give partial steps, and help the student reason through the problem.",
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
<!DOCTYPE html>
<!DOCTYPE html>
<html>
<head>
    <title>ACE Tutor</title>

    <!-- Import Anton font -->
    <link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">

    <style>
        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            width: 100vw;
            font-family: "Inter", Arial, sans-serif;

            /* Balanced dark background */
            background: radial-gradient(circle at 20% 20%, #ffffff2a, #000000aa),
                        linear-gradient(135deg, #4a12b8, #2a4fe0, #ff4eb8);
            background-size: 300% 300%;
            animation: gradientShift 16s ease infinite;
            overflow: hidden;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* MAIN GLASS CHAT BOX */
        .chat-container {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;

            margin: auto;
            width: 80%;
            max-width: 900px;
            height: 90%;

            backdrop-filter: blur(40px) saturate(200%);
            background: rgba(255, 255, 255, 0.12);
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.32);

            box-shadow:
                0 0 45px rgba(255, 255, 255, 0.18),
                inset 0 0 30px rgba(255, 255, 255, 0.12);
        }

        .header {
            padding: 20px;
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            color: white;
            background: rgba(255, 255, 255, 0.10);
            border-bottom: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 28px 28px 0 0;
        }

        /* SETTINGS */
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
            font-size: 14px;
            font-weight: 600;
            color: white;
            margin-bottom: 6px;
        }

        .settings select {
            appearance: none;
            padding: 14px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.32);
            background: rgba(255, 255, 255, 0.20);
            color: white;
            font-size: 16px;
            outline: none;
            cursor: pointer;
            backdrop-filter: blur(20px);

            background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='18' viewBox='0 0 24 24' width='18' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
            background-repeat: no-repeat;
            background-position: right 14px center;
            background-size: 18px;
        }

        /* CHAT AREA */
        #chat {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        /* INTRO TEXT (not a bubble) */
        .intro-text {
            font-family: 'Anton', sans-serif;
            font-size: 38px;
            letter-spacing: 0.5px;
            color: white;
            opacity: 0;
            animation: fadeInIntro 0.8s ease forwards;
            margin-bottom: 18px;
            margin-left: 6px;
        }

        @keyframes fadeInIntro {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg {
            padding: 16px 20px;
            border-radius: 18px;
            max-width: 70%;
            line-height: 1.5;
            font-size: 17px;
            color: white;

            background: rgba(255, 255, 255, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.40);
            backdrop-filter: blur(25px);

            box-shadow:
                inset 0 0 18px rgba(255, 255, 255, 0.18),
                0 4px 14px rgba(0,0,0,0.25);

            animation: fadeIn 0.25s ease-out;

            display: flex;
            flex-direction: column;
        }

        .msg.user {
            align-self: flex-end;
            background: rgba(120, 180, 255, 0.38);
        }

        .msg.ai {
            align-self: flex-start;
        }

        /* TIMESTAMP */
        .timestamp {
            font-size: 12px;
            opacity: 0.75;
            color: #eaeaea;
            margin-top: 10px;
            display: block;
        }

        .msg.user .timestamp { text-align: right; }
        .msg.ai .timestamp { text-align: left; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* INPUT AREA */
        .input-area {
            display: flex;
            justify-content: center;
            padding: 22px 0;
            background: rgba(255, 255, 255, 0.09);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 0 0 28px 28px;
        }

        .input-wrapper {
            display: flex;
            width: 60%;
            max-width: 600px;
            gap: 14px;
        }

        #msg {
            flex: 1;
            padding: 16px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.32);
            background: rgba(255, 255, 255, 0.20);
            color: white;
            outline: none;
            font-size: 19px;
        }

        #msg::placeholder {
            color: rgba(255, 255, 255, 0.7);
            font-size: 19px;
        }

        /* SEND BUTTON — white text + very soft glow */
        #send {
            padding: 0 26px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            background: rgba(255, 255, 255, 0.28);
            color: white;
            cursor: pointer;
            transition: 0.25s;
            font-size: 18px;
        }

        #send:hover {
            background: rgba(255, 255, 255, 0.40);
            box-shadow: 0 0 3px rgba(255, 255, 255, 0.30),
                        0 0 6px rgba(255, 255, 255, 0.18);
        }
    </style>
</head>

<body>
    <div class="chat-container">
        <div class="header">ACE Tutor</div>

        <div class="settings">
            <div class="settings-group">
                <label>Mode:</label>
                <select id="mode">
                    <option value="normal">Normal</option>
                    <option value="tutor">Tutor (Hints Only)</option>
                </select>
            </div>

            <div class="settings-group">
                <label>Style:</label>
                <select id="style">
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="sarcastic">Sarcastic</option>
                    <option value="storyteller">Storyteller</option>
                </select>
            </div>
        </div>

        <div id="chat">
            <!-- INTRO TEXT (not a bubble) -->
            <div class="intro-text">Hey, what can I help with today?</div>
        </div>

        <div class="input-area">
            <div class="input-wrapper">
                <input id="msg" placeholder="Type your message...">
                <button id="send">Send</button>
            </div>
        </div>
    </div>

    <script>
        const chat = document.getElementById("chat");
        const msg = document.getElementById("msg");
        const send = document.getElementById("send");
        const style = document.getElementById("style");
        const mode = document.getElementById("mode");

        function timestamp() {
            const d = new Date();
            return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        }

        function addMessage(text, sender) {
            const div = document.createElement("div");
            div.className = "msg " + sender;

            const content = document.createElement("div");
            content.innerText = text;

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
        }

        send.onclick = sendMessage;

        msg.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
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





