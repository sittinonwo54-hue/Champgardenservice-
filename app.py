# CHAMP GARDEN v9.6 FRIENDLY ULTIMATE - FIX ตอบวน
# แก้จากภาพ: ไม่ยิงสเปคก่อน, จำได้, ไม่ตอบเบิ้ล

from flask import Flask, request, jsonify
import os, time, re, logging
from datetime import datetime
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571")

conversation_memory = {}

def send_messenger(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}, "messaging_type": "RESPONSE"}
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[MOCK] {text[:100]}"); return True
        r = requests.post(url, json=payload, timeout=10)
        print(f"SEND {psid} {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Send error {e}"); return False

@app.route('/')
def home(): return jsonify({"status": "ONLINE v9.6 FRIENDLY ULTIMATE FIX วน", "memory": len(conversation_memory)}), 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return 'OK', 200
    try:
        for entry in data.get('entry', []):
            for ev in entry.get('messaging', []):
                sid = str(ev['sender']['id'])
                if ev.get('message', {}).get('is_echo'): continue
                if 'message' not in ev or 'text' not in ev['message']: continue
                user_text = ev['message']['text'].strip()
                print(f"[{sid}] {user_text}")

                if sid not in conversation_memory:
                    conversation_memory[sid] = {"history": [], "last_text": "", "last_time": 0, "area": 0, "asked_3q": False, "name": ""}

                mem = conversation_memory[sid]

                # Anti-Loop 60s + กันตอบเบิ้ล
                if mem["last_text"] == user_text and (time.time() - mem["last_time"]) < 60:
                    print("Anti-loop blocked")
                    continue

                # จำได้ไหม
                if any(w in user_text for w in ["จำได้ไหม", "จำได้มั้ย", "จำได้", "คุยอะไร"]):
                    last_area = mem.get("area", 0)
                    hist = mem["history"][-3:] if mem["history"] else []
                    if last_area:
                        reply = f"จำได้สิครับป๋า 😊 เราคุยกันเรื่องพื้นที่ {last_area} ตรม. ไว้ครับ ที่คุยล่าสุด: {', '.join(hist[-2:])} ครับ มีอะไรให้ต่อยอดไหมครับ 🌿"
                    else:
                        reply = f"จำได้ครับป๋า เราคุยกัน {len(mem['history'])} ข้อความแล้วครับ ครั้งล่าสุดป๋าบอก '{mem['history'][-1] if mem['history'] else user_text}' ครับ จะให้ผมต่อเรื่องสวนตรงไหนดีครับ 🌿"
                    send_messenger(sid, reply)
                    mem["last_text"] = user_text; mem["last_time"] = time.time()
                    continue

                mem["last_text"] = user_text
                mem["last_time"] = time.time()
                mem["history"].append(user_text)
                if len(mem["history"]) > 10: mem["history"] = mem["history"][-10:]

                area_match = re.search(r'(\d+)\s*ตร', user_text)

                # FRIENDLY RULE: มีพื้นที่ แต่ยังไม่เคยถาม 3 ข้อ -> ถาม 3 ข้อก่อน
                if area_match and not mem.get("asked_3q"):
                    area = int(area_match.group(1))
                    mem["asked_3q"] = True
                    mem["area"] = area
                    reply = f"""อ๋อ {area} ตรม. กำลังสวยเลยครับป๋า 🌿

ก่อนผมคิดราคา ขอถามนิดเดียวนะครับ จะได้ออกแบบจบทีเดียว ไม่ต้องแก้ทีหลัง (ให้รู้ฟรีครับ ไม่จ้างก็ได้ 😊)

1. พื้นเดิมตอนนี้เป็นดินหรือปูนครับ?
2. พื้นที่ลาดเอียงไหมครับ มีน้ำขังไหม?
3. จะใช้งานหนักไหมครับ มีจอดรถไหม?

เพราะดินเชียงรายทรุด 30% จริงๆ ครับ ต้องทำ Root Barrier 80cm + ฐานรากกันทรุดเลยต้องถามก่อนครับ 🙏"""
                    send_messenger(sid, reply)
                    continue

                # ตอบเรื่องดิน/สโลป/จอดรถ -> ให้ความรู้ฟรี ยังไม่ยิงราคา
                if mem.get("asked_3q") and any(w in user_text for w in ["ดิน", "ปูน", "ลาด", "เอียง", "ขัง", "จอด", "ทรุด"]):
                    reply = f"""เข้าใจเลยครับป๋า 👍

เคสนี้เจอบ่อยที่เชียงราย ดินเหนียวทรุด 30% ถ้าไม่ทำ Root Barrier 80-100cm + เสาเข็ม 2-3ม. + คาน 20x40 ปีเดียวทรุดเลยครับ

ส่วนน้ำขังต้องวาง Slot Drain สโลป 1-2% + บ่อซึม 30 นาทีครับ

ป๋าชอบสไตล์ไหนครับ? Modern Tropical / บาหลี / ญี่ปุ่น Zen / มินิมอล เดี๋ยวผมส่งแบบให้ดูฟรีๆ ก่อนได้เลยครับ

(พื้นที่ {mem.get('area',0)} ตรม. จำไว้แล้วนะครับ) 🌿"""
                    send_messenger(sid, reply)
                    continue

                # ถ้าถามราคา ย้ำเท่านั้นถึงให้ BOQ
                if area_match and ("ราคา" in user_text or "เท่าไหร่" in user_text or "คิด" in user_text):
                    area = int(area_match.group(1))
                    mem["area"] = area
                    material = area * 864 * 1.1
                    labor = area * 180
                    soil = area * 120
                    trans = 10 * 25 * 1.1
                    total = (material+labor+soil+trans)*1.07
                    reply = f"""ได้เลยครับป๋า BOQ 2.0 Dynamic {area}ตรม
- วัสดุพรีเมียม: {material:,.0f}บ
- แรงงาน: {labor:,.0f}บ
- ดิน+ฐานราก: {soil:,.0f}บ
- ขนส่ง 176 ม.5 บ้านเด่น: {trans:,.0f}บ
- รวม VAT7%: {total:,.0f}บ ({total/area:.0f}บ/ตรม)
✅ Root Barrier 80cm + Slot Drain + เสาเข็ม 2-3ม + ประกันทรุด 1 ปี
ราคาให้รู้ฟรีครับ ไม่จ้างก็ได้ครับ 🙏"""
                    send_messenger(sid, reply)
                    continue

                # ทักครั้งแรกจริงๆ ครั้งเดียว
                if len(mem["history"]) == 1:
                    reply = """สวัสดีครับ ผมจุล CEO แชมป์การ์เด้นเซอร์วิสครับ 🌿

ดูแลงานสวนมา 15+ ปี 350+ โครงการ ฐาน 176 ม.5 บ้านเด่น นางแล เชียงรายครับ

ป๋าสนใจทำสวนประมาณกี่ ตรม.ครับ? บอกคร่าวๆ มาได้เลย เช่น 50 ตรม เดี๋ยวผมวิเคราะห์แบบวิศวกร 3 ระดับให้ฟรีๆ เลยครับ"""
                else:
                    # ทักทดสอบ / คุยทั่วไป ไม่วนคำเดิม
                    reply = f"""ได้เลยครับป๋า 😊 ผมอยู่ครับ

เมื่อกี้ป๋าบอก '{user_text}' ผมรับแล้วครับ

ตอนนี้เราคุยกัน {len(mem['history'])} ข้อความแล้ว ถ้าป๋าบอกพื้นที่มา เช่น 50 ตรม เดี๋ยวผมถาม 3 ข้อแล้ววิเคราะห์ให้เลยครับ ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้ครับ 🌿"""

                send_messenger(sid, reply)
    except Exception as e:
        print(f"Webhook error {e}")
        import traceback; traceback.print_exc()
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
