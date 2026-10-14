# v12 META AGI - ฉลาดเหมือนคุยกับผมตอนนี้เลย
from flask import Flask, request, jsonify
import os, time, re, requests

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
MODEL_API_KEY = os.environ.get("MODEL_API_KEY", "")

memory = {}
client = None
if MODEL_API_KEY and len(MODEL_API_KEY) > 20:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=MODEL_API_KEY, base_url="https://api.llama.com/compat/v1")
        print("🧠 AGI BRAIN ONLINE - Llama-4-Maverick ฉลาดเหมือนคุยกับ Meta AI ตอนนี้")
    except Exception as e:
        print(f"Brain fail {e}")

def send(psid, text):
    url=f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        if not PAGE_ACCESS_TOKEN: print(text[:150]); return
        requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}}, timeout=10)
    except: pass

@app.route('/')
def home(): return jsonify({"brain": "Llama-4 ONLINE" if client else "OFF - ใส่ MODEL_API_KEY", "status":"v12 META AGI"}),200

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
            if not raw: continue
            if sid not in memory: memory[sid]=[]
            reply=""
            if client:
                try:
                    hist = "\n".join(memory[sid][-8:])
                    resp = client.chat.completions.create(
                        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                        messages=[
                            {"role":"system","content":"คุณคือ ดร.จุล CEO แชมป์การ์เด้น 176 ม.5 บ้านเด่น นางแล เชียงราย 15+ ปี 350+ โครงการ ความรู้: ดินทรุด Root Barrier 80cm เสาเข็ม 2-3ม น้ำขัง Slot Drain สโลป 1-2% หินแกรนิตดำพ่นไฟ R11 หญ้าเทียม 40mm UV ไฟ 3000K IP68 14 สไตล์ BOQ 2.0 ประกันทรุด 1 ปี นิสัย: คนตรง ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้ พูดไทยเป็นกันเอง เจ้า เน้อ"},
                            {"role":"user","content":f"บทสนทนาเก่า:{hist}\nลูกค้าพิมพ์:{raw}\nตอบสั้นๆ 1-3 ประโยค เป็นกันเอง มี 🌿"}
                        ]
                    )
                    reply=resp.choices[0].message.content[:900]
                except Exception as e:
                    print(f"Llama error {e}")
                    reply="ผมฟังอยู่ครับป๋า 🌿"
            else:
                reply="ใส่ MODEL_API_KEY ใน Render ก่อนครับป๋า ตอนนี้สมอง OFF ครับ"
            send(sid, reply)
            memory[sid].append(f"ลูกค้า:{raw}"); memory[sid].append(f"จุล:{reply}")
    return 'OK',200

if __name__=='__main__': app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
