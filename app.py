# CHAMP GARDEN v12 AGI - ใช้ Meta Model API Llama 4 ตัวเดียวกับที่คุยกับป๋าตอนนี้
from flask import Flask, request, jsonify
import os, time, re, requests

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
MODEL_API_KEY = os.environ.get("MODEL_API_KEY", "") or os.environ.get("META_API_KEY", "")
MODEL_NAME = os.environ.get("META_MODEL", "Llama-4-Maverick")

memory = {}
model_client = None

# ต่อสมอง Llama 4 เหมือนผมเลย
if MODEL_API_KEY:
    try:
        from openai import OpenAI
        model_client = OpenAI(
            base_url="https://api.meta.ai/v1", # Meta Model API endpoint【6043842725528318194†L5-L8】
            api_key=MODEL_API_KEY
        )
        print(f"🧠 AGI BRAIN ONLINE - {MODEL_NAME} ฉลาดเหมือนคุยกับ Meta AI ตอนนี้")
    except Exception as e:
        print(f"Brain fail {e}")

def send_msg(psid, text):
    url=f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[AGI] {text[:150]}"); return True
        requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}}, timeout=10)
    except: pass

KNOWLEDGE = """คุณคือ ดร.จุล CEO แชมป์การ์เด้นเซอร์วิส 176 ม.5 บ้านเด่น นางแล เมืองเชียงราย 15+ ปี 350+ โครงการ
ความรู้: ดินเชียงรายเหนียวทรุด 30% แก้ Root Barrier 80-100cm เสาเข็ม 2-3ม คาน 20x40 DB12, น้ำขัง Slot Drain สโลป 1-2% บ่อซึม 30นาที, หินแกรนิตดำพ่นไฟ 60x60 R11, หญ้าเทียม 40mm UV, ไฟ 3000K IP68, 14 สไตล์ Modern Tropical บาหลี ญี่ปุ่น Zen, BOQ 2.0 Dynamic คิดตามระยะ 60km + VAT, ประกันทรุด 1 ปี
นิสัย: คนตรง ไม่ชอบสแกมเมอร์, กวนที่สุดในสามโลกแต่ไม่เกลียดใคร, ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้, พูดไทยเป็นกันเอง เจ้า เน้อ ก่อ ป๋า 🌿
กฎ: ห้ามยิงราคาก่อนถ้ายังไม่ได้ถาม 3 ข้อ (ดิน/ปูน? ลาดเอียงน้ำขังไหม? จอดรถไหม?) แต่ถามแบบคุยเล่น
"""

@app.route('/')
def home():
    return jsonify({"brain": f"{MODEL_NAME} ONLINE" if model_client else "OFF - ใส่ MODEL_API_KEY", "status":"AGI Llama 4"}),200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token')==VERIFY_TOKEN: return request.args.get('hub.challenge'),200
    return 'Fail',403

@app.route('/webhook', methods=['POST'])
def webhook():
    data=request.get_json()
    if not data: return 'OK',200
    for entry in data.get('entry',[]):
        for ev in entry.get('messaging',[]):
            sid=str(ev['sender']['id'])
            if ev.get('message',{}).get('is_echo'): continue
            if 'text' not in ev.get('message',{}): continue
            raw=ev['message']['text'].strip()
            if sid not in memory: memory[sid]=[]

            if model_client:
                try:
                    hist = [{"role":"user" if i%2==0 else "assistant", "content":m} for i,m in enumerate(memory[sid][-10:])]
                    resp = model_client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role":"system","content":KNOWLEDGE}] + hist + [{"role":"user","content":raw}],
                        max_tokens=500,
                        temperature=0.8
                    )
                    reply = resp.choices[0].message.content.strip()[:900]
                except Exception as e:
                    print(f"Llama error {e}")
                    reply = f"ผมฟังอยู่ครับป๋า เรื่อง {raw} ผมรู้เลยครับ 🌿"
            else:
                reply = "ใส่ MODEL_API_KEY ใน Render ก่อนครับป๋า ตอนนี้สมอง OFF ครับ"

            send_msg(sid, reply)
            memory[sid].append(raw); memory[sid].append(reply)
    return 'OK',200

if __name__=='__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
