import os
import time
import base64
import io
import requests
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from PIL import Image

app = Flask(__name__)

# --- KEYS ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- 1. VISION LOGIC (ANKHEIN) ---
def analyze_image_with_gemini(image_data, user_prompt):
    try:
        # Base64 string ko Image mein convert karo
        image_parts = image_data.split(",")
        image_str = image_parts[1] if len(image_parts) > 1 else image_parts[0]
        
        img_bytes = base64.b64decode(image_str)
        img = Image.open(io.BytesIO(img_bytes))

        # Gemini Vision Model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt ko adjust karo taaki wo explain kare
        if not user_prompt:
            user_prompt = "Explain this image in detail in Hinglish."
        
        response = model.generate_content([user_prompt, img])
        return response.text
    except Exception as e:
        print(f"Vision Error: {e}")
        return "Photo saaf nahi hai ya format galat hai. Dubara bhejo."

# --- 2. TEXT BRAIN (GROQ) ---
def ask_groq(prompt):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful AI. Reply in Hinglish."},
                {"role": "user", "content": prompt}
            ],
            "model": "llama-3.3-70b-versatile"
        }
        resp = requests.post(url, headers=headers, json=data)
        return resp.json()['choices'][0]['message']['content']
    except: return None

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    msg = data.get('message', '')
    image_data = data.get('image') # Frontend se image aayegi
    
    response = {"type": "text", "content": ""}

    # SCENARIO 1: AGAR IMAGE HAI (Vision Mode)
    if image_data:
        reply = analyze_image_with_gemini(image_data, msg)
        response["content"] = reply

    # SCENARIO 2: IMAGE GENERATION (Creation Mode)
    elif "/image" in msg.lower() or ("photo" in msg.lower() and "banao" in msg.lower()):
        clean_prompt = msg.replace("/image", "").replace("photo banao", "").strip()
        img_url = f"https://pollinations.ai/p/{clean_prompt}?width=1280&height=720&model=flux&seed={int(time.time())}&nologo=true"
        response["type"] = "image"
        response["content"] = img_url
        response["text"] = f"Ye lo {clean_prompt} ki photo."

    # SCENARIO 3: NORMAL CHAT
    else:
        reply = ask_groq(msg)
        # Fallback to Gemini if Groq fails
        if not reply:
            model = genai.GenerativeModel('gemini-1.5-flash')
            reply = model.generate_content(msg).text
            
        response["content"] = reply if reply else "Server busy hai."

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)0
