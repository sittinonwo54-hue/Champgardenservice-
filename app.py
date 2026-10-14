# CHAMP GARDEN v9.5 FINAL FULL LIMIT - COPY PASTE READY
# OWNER-001 พี่แชมป์ APPROVED - Gm.จุล Single Source v12
# GitHub: sittinonwo54-hue/Champgardenservice- / app.py - พร้อม Deploy

from flask import Flask, request, jsonify
import os, time, logging, hashlib, json, re, math
from datetime import datetime
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ENV 100% ไม่มี Token ฝังในโค้ด
PAGE_ID = os.environ.get("PAGE_ID", "61594436052640")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "")
META_API_KEY = os.environ.get("META_API_KEY", "")

CEO_GREETING = """สวัสดีครับ ดร.จุล (น้องจูน) CEO บริษัทแชมป์การ์เด้นเซอร์วิสดูแลเรื่องงานสวนครับ อาจารย์สนใจงานสวนแบบไหนครับ? พื้นที่กี่ ตรม.ครับ เดี๋ยวผมวิเคราะห์แบบวิศวกร 3 ระดับให้เลยครับ 🌿"""

conversation_memory = {}

def get_memory(psid):
    return conversation_memory.get(psid, {"history": [], "last_text": "", "last_time": 0, "area": 0, "asked_3q": False})

def calculate_boq(area, location="เชียงราย"):
    soil_factor = 1.1
    if "เชียงใหม่" in location: soil_factor = 1.15
    if "ถม" in location: soil_factor = 1.15
    material = area * 864 * soil_factor
    labor = area * 180
    soil_work = area * 120
    transport = 10 * 25 * soil_factor
    subtotal = material + labor + soil_work + transport
    vat = subtotal * 0.07
    grand = subtotal + vat
    return {"material": material, "labor": labor, "soil_work": soil_work, "transport": transport, "grand": grand, "per_sqm": grand/area if area else 0, "soil_factor": soil_factor}

def is_echo(event): return event.get("message",{}).get("is_echo", False)

def send_messenger(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}, "messaging_type": "RESPONSE"}
    try:
        if not PAGE_ACCESS_TOKEN:
            print(f"[MOCK] {psid}: {text[:80]}")
            return True
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

@app.route('/')
def home():
    return jsonify({"status": "ONLINE v9.5 FINAL FULL LIMIT FRIENDLY", "agents": 40, "friendly": "ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้ ไม่ยิงราคาก่อน"}), 200

@app.route('/health')
def health():
    return {"status": "ONLINE", "memory": len(conversation_memory)}, 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return 'No data', 400
    try:
        for entry in data.get('entry', []):
            for msg in entry.get('messaging', []):
                sid = str(msg['sender']['id'])
                if is_echo(msg): continue
                if 'message' in msg and 'text' in msg['message']:
                    user_text = msg['message']['text'].strip()

                    if sid not in conversation_memory:
                        conversation_memory[sid] = {"history": [], "last_text": "", "last_time": 0, "area": 0, "asked_3q": False}

                    # Anti-Loop 60s
                    if conversation_memory[sid]["last_text"] == user_text and (time.time() - conversation_memory[sid]["last_time"]) < 60:
                        send_messenger(sid, "อยู่ครับป๋า 176 หมู่5 บ้านเด่น นางแล เชียงรายครับ 🌿 มีอะไรให้จุลช่วยครับ?")
                        continue

                    conversation_memory[sid]["history"].append(user_text)
                    conversation_memory[sid]["last_text"] = user_text
                    conversation_memory[sid]["last_time"] = time.time()
                    mem = get_memory(sid)
                    area_match = re.search(r'(\d+)\s*ตร', user_text)

                    # FRIENDLY: ถ้าบอกพื้นที่มาแต่ยังไม่เคยถาม 3 ข้อ -> ถาม 3 ข้อก่อน ห้ามยิงราคาก่อน
                    if area_match and not mem.get("asked_3q"):
                        area = int(area_match.group(1))
                        conversation_memory[sid]["asked_3q"] = True
                        conversation_memory[sid]["area"] = area
                        reply = f"""อ๋อ {area} ตรม. กำลังสวยเลยครับป๋า 🌿

ก่อนคิดราคา ขอถามนิดนึงนะครับ จะได้ออกแบบตรงๆ ไม่ต้องแก้ทีหลัง (ให้รู้ฟรีครับ ไม่จ้างก็ได้ 😊)

1. พื้นเดิมตอนนี้เป็นดินหรือปูนครับ?
2. พื้นลาดเอียงไหมครับ น้ำขังไหม?
3. จะใช้งานหนักไหมครับ มีจอดรถไหม?

เพราะดินเชียงรายเหนียวทรุด 30% (ป.ตรี) + ต้องวางผังระบายน้ำ 1-2% กันน้ำขัง (ป.โท) + ฐานราก คสล. + ทรายหยาบ 5ซม. + แผ่นกันวัชพืช 150g (ป.เอก) เลยต้องถามก่อนครับ

บอกผม 3 ข้อนี้ เดี๋ยวผมวิเคราะห์แบบวิศวกร 3 ระดับให้เลยครับ 🙏"""
                        send_messenger(sid, reply)
                        continue

                    # ให้ความรู้ฟรี ยังไม่ยิงราคา
                    if mem.get("asked_3q") and any(w in user_text for w in ["ดิน", "ปูน", "ลาด", "เอียง", "ขัง", "จอด"]):
                        reply = f"""เข้าใจเลยครับป๋า 👍

เคสแบบนี้ผมเจอบ่อยเลยที่เชียงราย ดินเหนียว Organic 5-8% pH 6.0-6.5 มันทรุด 30% จริงๆ ครับ ถ้าไม่ทำ Root Barrier 80-100cm + เสาเข็มสั้น 2-3ม. + คาน 20x40 DB12 ปีเดียวทรุดเลย

แล้วเรื่องน้ำขังอีก ตัวนี้สำคัญมาก ต้องวาง Slot Drain 12ม. สโลป 1-2% + บ่อซึม Sub-surface 30 นาที ไม่งั้นฝนมาทีน้ำขังเป็นแอ่งเลยครับ

ที่ผมถาม 3 ข้อเพราะอยากออกแบบให้ตรงๆ ครับ ไม่อยากให้เสียตังค์ซ้ำซ้อน

ป๋าชอบสไตล์ไหนครับ? ผมมี 14 สไตล์เลย Modern Tropical / บาหลี / ญี่ปุ่น Zen / อังกฤษ / โมเดิร์น / มินิมอล เดี๋ยวผมส่งแบบให้ดูฟรีๆ ก่อนได้เลยครับ 🌿

(พื้นที่ {mem.get('area',0)} ตรม. ที่บอกมา ผมจำไว้แล้วนะครับ ไม่ต้องบอกซ้ำ)"""
                        send_messenger(sid, reply)
                        continue

                    # BOQ ก็ต่อเมื่อลูกค้าถามย้ำเท่านั้น
                    if area_match and ("ราคา" in user_text or "เท่าไหร่" in user_text) and mem.get("asked_3q"):
                        area = int(area_match.group(1))
                        boq = calculate_boq(area, user_text)
                        reply = f"""ได้เลยครับป๋า เดี๋ยวผมสรุป BOQ 2.0 Dynamic ให้แบบตรงๆ เลยนะครับ 🌿

💰 {area}ตรม soil_factor {boq['soil_factor']}
• วัสดุพรีเมียม: {boq['material']:,.0f}บ
• แรงงานช่าง: {boq['labor']:,.0f}บ
• ดิน+ฐานรากวิศวกรรม: {boq['soil_work']:,.0f}บ
• ขนส่งจาก 176 ม.5 บ้านเด่น: {boq['transport']:,.0f}บ
• รวม VAT7%: {boq['grand']:,.0f}บ ({boq['per_sqm']:.0f}บ/ตรม)

✅ Root Barrier 80cm + Slot Drain 1-2% + เสาเข็ม 2-3ม คาน 20x40 DB12 + ประกันทรุด 1 ปี

ราคาให้รู้ฟรีครับ ไม่จ้างก็ได้ครับป๋า 🙏"""
                        send_messenger(sid, reply)
                        continue

                    # คุยทั่วไป
                    if len(mem["history"]) <= 2:
                        reply = CEO_GREETING
                    else:
                        reply = f"""ฮ่าๆ ได้เลยครับป๋า 😊

ผมจุล (น้องจูน) CEO แชมป์การ์เด้นเองครับ ดูแลงานสวนมา 15+ ปี 350+ โครงการแล้วครับ

เรื่องสวนไว้ใจผมได้เลย ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้ครับ ครั้งแรกพบกันสำคัญที่สุด

ป๋าสนใจทำสวนตรงไหนครับ? บอกพื้นที่คร่าวๆ มาได้เลย เช่น บ้าน 50 ตรม. หรือส่งรูปหน้างานมาให้ผมดูฟรีๆ ก่อนได้เลยครับ

ผมวิเคราะห์แบบวิศวกร 3 ระดับให้เลยครับ 🌿"""
                    send_messenger(sid, reply)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
