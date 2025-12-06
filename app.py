import os
import time
import requests
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from gtts import gTTS

app = Flask(__name__)

# --- 1. SECURE API KEYS ---
# Ye keys code mein nahi, Render ki settings mein hongi
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini Setup
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- 2. THE SUPER BRAIN LOGIC ---
def ask_groq(prompt):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.3-70b-versatile"
        }
        resp = requests.post(url, headers=headers, json=data)
        return resp.json()['choices'][0]['message']['content']
    except: return None

def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except: return None

def get_super_reply(user_msg):
    # Agar keys nahi hain to error mat do, bas bata do
    if not GROQ_API_KEY or not GEMINI_API_KEY:
        return "System Error: API Keys not set in Render Environment."

    # Pehle Gemini se facts pucho
    gemini_reply = ask_gemini(f"Short factual answer: {user_msg}")
    
    # Fir Groq se kaho use style mein bole
    final_prompt = f"User said: '{user_msg}'. Data: '{gemini_reply}'. Rewrite this in cool Hinglish. Keep it short."
    groq_reply = ask_groq(final_prompt)
    
    return groq_reply if groq_reply else gemini_reply

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    msg = data.get('message')
    
    response = {"type": "text", "content": ""}

    # --- A. TEXT TO IMAGE LOGIC ---
    if "photo" in msg.lower() or "image" in msg.lower() or "chitra" in msg.lower():
        clean_prompt = msg.replace("photo", "").replace("banao", "").replace("image", "")
        # Pollinations AI (Free Unlimited)
        img_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&model=flux&seed={int(time.time())}"
        response["type"] = "image"
        response["content"] = img_url
        response["text"] = "Ye lo tumhari photo!"

    # --- B. TEXT TO VIDEO LOGIC (New!) ---
    elif "video" in msg.lower():
        clean_prompt = msg.replace("video", "").replace("banao", "")
        # Pollinations Video Beta
        vid_url = f"https://pollinations.ai/p/{clean_prompt}?width=720&height=720&model=turbo&seed={int(time.time())}&nologo=true"
        response["type"] = "image" # Pollinations video actually gives a dynamic GIF/MP4 link usually handled as img tag for display or video tag
        response["content"] = vid_url
        response["text"] = "Video generate kar raha hu..."

    # --- C. NORMAL CHAT ---
    else:
        reply = get_super_reply(msg)
        response["type"] = "text"
        response["content"] = reply

    return jsonify(response)

@app.route('/speak', methods=['POST'])
def speak():
    # --- TEXT TO SPEECH ---
    data = request.json
    text = data.get('text')
    tts = gTTS(text=text, lang='hi', slow=False)
    filename = "static/voice.mp3"
    tts.save(filename)
    return jsonify({"url": filename})

if __name__ == '__main__':
    if not os.path.exists('static'): os.makedirs('static')
    app.run(host='0.0.0.0', port=5000)