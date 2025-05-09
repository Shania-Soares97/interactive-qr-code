from flask import Flask, render_template, request, jsonify
from googletrans import Translator
from gtts import gTTS
import requests
import os
import psycopg2

app = Flask(__name__)

# Chatbot Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"

# ---------- TEXT & TTS FUNCTIONS ----------
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tts_text (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tts_text")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO tts_text (content) VALUES (%s)", ("Easter Island, or Rapa Nui, is a remote volcanic island in the southeastern Pacific Ocean, part of Chile. It is world-famous for its massive stone statues called moai, created by the island’s early Polynesian inhabitants.
                                                                      The moai are believed to represent ancestral figures and hold great cultural and spiritual meaning.
                                                                      Today, Easter Island is a UNESCO World Heritage Site and a major archaeological and tourist destination.",))
    conn.commit()
    conn.close()

def fetch_text_from_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM tts_text ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "No text found."

def translate_text(text, target_lang):
    translator = Translator()
    translated = translator.translate(text, src='en', dest=target_lang)
    return translated.text

def generate_audio(text, lang_code):
    tts = gTTS(text, lang=lang_code)
    filename = f"static/audio_{lang_code}.mp3"
    tts.save(filename)
    return filename

# ---------- MAIN PAGE ----------
@app.route("/", methods=["GET", "POST"])
def home():
    text = fetch_text_from_db()
    translated_text = text
    audio_file = None

    if request.method == "POST":
        lang = request.form["language"]
        translated_text = translate_text(text, lang)
        audio_file = generate_audio(translated_text, lang)

    return render_template("index.html", translated=translated_text, audio=audio_file)

# ---------- CHATBOT ENDPOINT ----------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Please keep your responses limited to 1 paragraph. Respond in the language you receive the question in."},
        {"role": "user", "content": user_message}
    ]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": conversation
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        bot_reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- INIT DB ----------
init_db()

if __name__ == '__main__':
    app.run(debug=True)
