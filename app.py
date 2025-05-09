from flask import Flask, render_template, request, jsonify
import sqlite3
from googletrans import Translator
from gtts import gTTS
import requests
import os

app = Flask(__name__)

# Chatbot Config
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"

# ---------- TEXT & TTS FUNCTIONS ----------
def fetch_text_from_db():
    conn = sqlite3.connect("texts.db")
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
        {"role": "system", "content": "You are a helpful assistant. Please keep your responses limited to 1 paragraph. Respond in the language you recieve the question in"},
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

if __name__ == '__main__':
    app.run(debug=True, port=5004)
