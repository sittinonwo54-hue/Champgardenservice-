import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ========== ENV - อ่านได้ทุกชื่อ ==========
GOOGLE_URL = os.getenv("GOOGLE_SCRIPT_URL") or "https://script.google.com/macros/s/AKfycbzAblPPHizhVLyCu5dvvOv6rv4LFVq4mIXF24Kg1jh0jSLoBrAkXso9ORgZf7Dwsj7a/exec"
CHAMP_KEY = os.getenv("CHAMP_KEY") or "CHAMP-SECRET-KEY-2026-GLOBAL-60"

MODEL_API_KEY = (
    os.getenv("MODEL_API_KEY") or 
    os.getenv("GEMINI_API_KEY") or 
    os.getenv("Gemini_API_Key") or
    os.getenv("GENAI_API_KEY") or
    os.getenv("Gemini_API_key") or ""
)

PAGE_TOKEN = os.getenv("PAGE_ACCESS_TOKEN") or ""
PAGE_ID = os.getenv("PAGE_ID") or "61594436052640"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "champ_garden_verify_2026"

# ========== Gemini Setup ==========
gemini_model = None
brain_status = "OFF"
try:
    import google.generativeai as genai
    if MODEL_API_KEY:
        genai.configure(api_key=MODEL_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        brain_status = f"ON - {MODEL_API_KEY[:8]}... AQ OK"
        print(f"✅ BRAIN ON: {brain_status}")
    else:
        print("❌ BRAIN OFF: No MODEL_API_KEY")
except Exception as e:
    print(f"❌ BRAIN OFF Import Error: {e}")
    brain_status = f"OFF - {e}"

# ========== Call Champ Server 60 คน ==========
def call_champ_server(text):
    try:
        if not GOOGLE_URL:
            return "เซิร์ฟยังไม่ตั้ง GOOGLE_SCRIPT_URL ใน Render"
        url = f"{GOOGLE_URL}?key={CHAMP_KEY}&action=global&text={requests.utils.quote(text)}"
        print(f"CALLING CHAMP SERVER: {url[:120]}...")
        r = requests.get(url, timeout=20)
        data = r.json()
        # รองรับหลายรูปแบบ response
        if 'boq' in data:
            total = data['boq'].get('grand_total', data['boq'].get('total', 'N/A'))
            count = data.get('agents_count', data.get('total_agents', 60))
            return f"📊 ประเมินจากเซิร์ฟ {count} คน: {total} บาท"
        else:
            return f"เซิร์ฟตอบ: {str(data)[:300]}"
    except Exception as e:
        print(f"CHAMP SERVER ERROR: {e}")
        return f"เซิร์ฟ 60 คนกำลังบูท: {e}"

# ========== Send Facebook ==========
def send_fb_message(recipient_id, text):
    try:
        url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/messages?access_token={PAGE_TOKEN}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text[:1900]}
        }
        r = requests.post(url, json=payload, timeout=10)
        print(f"FB SEND: {r.status_code} {r.text[:200]}")
        return r.json()
    except Exception as e:
        print(f"FB SEND ERROR: {e}")
        return None

# ========== Routes ==========
@app.route('/')
def home():
    return f"""
    <h2>🌿 Champ Garden Service v12.5 - Server + Render</h2>
    <p>BRAIN: {brain_status}</p>
    <p>GOOGLE_URL: {'SET' if GOOGLE_URL else 'NOT SET'}</p>
    <p>PAGE_ID: {PAGE_ID}</p>
    <p>PAGE_TOKEN: {'SET' if PAGE_TOKEN else 'NOT SET'}</p>
    <p>Server 60 คน: {GOOGLE_URL[:80]}...</p>
    <p style='color:green'>ระบบเซิร์ฟเวอร์และบอททำงานปกติครับ</p>
    """

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return challenge, 200
    else:
        return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print(f"WEBHOOK IN: {str(data)[:500]}")
        
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for event in entry.get('messaging', []):
                    sender_id = event['sender']['id']
                    if 'message' in event and 'text' in event['message']:
                        user_text = event['message']['text']
                        print(f"USER {sender_id}: {user_text}")
                        
                        # Gemini Reply
                        if gemini_model:
                            try:
                                prompt = f"คุณคือแอดมิน Champ Garden บริการจัดสวนแม่สาย เชียงราย ตอบเป็นกันเอง กระชับ มืออาชีพ ลูกค้าถามว่า: {user_text}"
                                response = gemini_model.generate_content(prompt)
                                gemini_reply = response.text
                            except Exception as e:
                                gemini_reply = f"ขออภัย ระบบกำลังบูท: {e}"
                                print(f"GEMINI ERROR: {e}")
                        else:
                            gemini_reply = f"รับทราบครับ: {user_text} (BRAIN OFF - ใส่ MODEL_API_KEY ใน Render)"
                        
                        # ถ้าถามราคา ให้เรียกเซิร์ฟ 60 คน
                        final_reply = gemini_reply
                        if any(k in user_text.lower() for k in ["ราคา", "ตรม", "ตร.ม", "บาท", "ประเมิน", "boq", "ตารางเมตร"]):
                            boq_info = call_champ_server(user_text)
                            final_reply = f"{gemini_reply}\n\n{boq_info}"
                        
                        send_fb_message(sender_id, final_reply)
        
        return "OK", 200
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
        return f"Error {e}", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
