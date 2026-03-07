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

    <!-- Prevent weird zooming on mobile -->
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

        /* CHAT BOX (desktop) */
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

        /* three-dot menu (desktop hidden, mobile shown) */
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

        /* SETTINGS (desktop) */
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
            -webkit-appearance: none;
            -moz-appearance: none;

            padding: 14px 40px 14px 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.35);

            background-color: rgba(255, 255, 255, 0.22);
            background-clip: padding-box;

            color: white;
            font-size: 16px;
            cursor: pointer;
            backdrop-filter: blur(18px);

            background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='18' viewBox='0 0 24 24' width='18' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 18px;
        }

        .settings select::-ms-expand {
            display: none;
        }

        /* CHAT AREA */
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

        /* INPUT BAR (desktop) */
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
            opacity: 1 !important;
        }

        #msg:focus {
            outline: none !important;
            box-shadow: none !important;
            background: rgba(255, 255, 255, 0.28);
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

        /* Bottom sheet overlay + sheet */
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
            -webkit-appearance: none;
            -moz-appearance: none;

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

        /* 📱 MOBILE COPILOT LAYOUT */
        @media (max-width: 600px) {

            body {
                overflow: auto; /* fix funky scrolling */
            }

            .chat-container {
                width: 100%;
                max-width: 100%;
                height: calc(100vh - 80px);
                margin-top: 0;
                border-radius: 0;
                border-left: none;
                border-right: none;
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

            .header-title {
                font-size: 16px;
            }

            #menuBtn {
                display: block;
            }

            .settings {
                display: none; /* hide desktop settings bar */
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

            /* FLOATING INPUT BAR, NO BOX BEHIND */
            .input-area {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                width: 100%;
                max-width: 100%;
                margin-top: 0;
                padding: 10px 10px 16px;
                background: transparent; /* remove box behind */
                z-index: 25;
            }

            .input-wrapper {
                max-width: 900px;
                margin: 0 auto;
                gap: 8px;
            }

            #msg {
                border-radius: 999px;
                padding: 14px 16px;
                font-size: 16px;
                background: rgba(0, 0, 0, 0.35);
            }

            #send {
                width: 46px;
                height: 46px;
                background: rgba(255, 255, 255, 0.30);
            }

            #send svg {
                width: 22px;
                height: 22px;
            }

            .disclaimer {
                display: none;
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

    <!-- Bottom sheet + overlay -->
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

        <div class="sheet-row">
            <label for="styleSheet">Style</label>
            <select id="styleSheet">
                <option value="friendly">Friendly</option>
                <option value="professional">Professional</option>
                <option value="sarcastic">Sarcastic</option>
                <option value="storyteller">Storyteller</option>
            </select>
        </div>

        <button class="sheet-close" id="sheetClose">Close</button>
    </div>

    <script>
        const chat = document.getElementById("chat");
        const msg = document.getElementById("msg");
        const send = document.getElementById("send");
        const style = document.getElementById("style");
        const mode = document.getElementById("mode");

        const modeSheet = document.getElementById("modeSheet");
        const styleSheet = document.getElementById("styleSheet");
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
            styleSheet.value = style.value;
        }

        function syncMainFromSheet() {
            mode.value = modeSheet.value;
            style.value = styleSheet.value;
        }

        modeSheet.addEventListener("change", syncMainFromSheet);
        styleSheet.addEventListener("change", syncMainFromSheet);

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
    style = request.json.get("style", "friendly")
    mode = request.json.get("mode", "normal")
    reply = ask_ai(user_msg, style, mode)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)








