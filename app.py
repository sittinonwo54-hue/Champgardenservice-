# v12.2 FINAL FIX - แก้ OFF MODEL_API_KEY
from flask import Flask, request, jsonify
import os, requests

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")

# อ่านคีย์ทุกชื่อที่ป๋าอาจตั้ง
MODEL_API_KEY = (os.environ.get("MODEL_API_KEY") or
                 os.environ.get("META_API_KEY") or
                 os.environ.get("LLAMA_API_KEY") or "").strip()
GENAI_API_KEY = (os.environ.get("GENAI_API_KEY") or
                 os.environ.get("GEMINI_API_KEY") or
                 os.environ.get("GOOGLE_API_KEY") or "").strip()

print(f"DEBUG ENV: MODEL_API_KEY len={len(MODEL_API_KEY)} GENAI len={len(GENAI_API_KEY)}")

llama_client = None
gemini_model = None
status_msgs = []

if MODEL_API_KEY and len(MODEL_API_KEY) > 10:
    try:
        from openai import OpenAI
        llama_client = OpenAI(api_key=MODEL_API_KEY, base_url="https://api.llama.com/compat/v1")
        status_msgs.append("Llama-4 ONLINE")
        print("✅ Llama OK")
    except Exception as e:
        print(f"❌ Llama init fail: {e}")
        status_msgs.append(f"Llama FAIL: {e}")
else:
    print("❌ NO MODEL_API_KEY found in env!")

if GENAI_API_KEY and len(GENAI_API_KEY) > 10:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GENAI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        status_msgs.append("Gemini ONLINE")
        print("✅ Gemini OK")
    except Exception as e:
        print(f"❌ Gemini fail: {e}")
else:
    print("⚠️ No GENAI_API_KEY")

def send_msg(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        if not PAGE_ACCESS_TOKEN:
            print(text[:200]); return
        requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}}, timeout=10)
    except Exception as e:
        print(e)

KNOWLEDGE = """คุณคือ ดร.จุล CEO แชมป์การ์เด้น 176 ม.5 บ้านเด่น นางแล เชียงราย 15+ปี 350+โครงการ ดินทรุด แก้ Root Barrier 80cm เสาเข็ม2-3ม Slot Drain 1-2% หินดำพ่นไฟ R11 หญ้า40mm UV ไฟ3000K IP68 14สไตล์ BOQ2.0 ประกันทรุด1ปี พูดไทยเป็นกันเอง เจ้า เน้อ ป๋า 🌿"""

@app.route('/')
def home():
    if not status_msgs:
        brain = "OFF - ใส่ MODEL_API_KEY ใน Render Environment แล้วกด Save + Manual Deploy"
    else:
        brain = " + ".join(status_msgs)
    return jsonify({
        "brain": brain,
        "status": "v12.2 FINAL HYBRID",
        "env_check": {
            "MODEL_API_KEY_len": len(MODEL_API_KEY),
            "GENAI_API_KEY_len": len(GENAI_API_KEY)
        }
    }), 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Fail', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return 'OK', 200
    for entry in data.get('entry', []):
        for ev in entry.get('messaging', []):
            sid = str(ev['sender']['id'])
            if ev.get('message', {}).get('is_echo'): continue
            if 'text' not in ev.get('message', {}): continue
            raw = ev['message']['text'].strip()
            if not raw: continue
            reply=""
            if llama_client:
                try:
                    resp=llama_client.chat.completions.create(
                        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                        messages=[{"role":"system","content":KNOWLEDGE},{"role":"user","content":raw}],
                        max_tokens=500, temperature=0.8)
                    reply=resp.choices[0].message.content.strip()[:900]
                except Exception as e:
                    print(f"Llama chat error {e}")
            if not reply and gemini_model:
                try:
                    reply=gemini_model.generate_content(f"{KNOWLEDGE}\nลูกค้า:{raw}").text[:900]
                except Exception as e:
                    print(f"Gemini chat error {e}")
            if not reply:
                reply="ผมฟังอยู่ครับป๋า เล่าเรื่องหน้างานมาได้เลยครับ 🌿"
            send_msg(sid, reply)
    return 'OK',200

if __name__=='__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
