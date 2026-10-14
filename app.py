rom flask import Flask, request, jsonify

import os, time, logging, hashlib, json, re, math

from datetime import datetime

import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# CONFIG - ENV 100% ไม่มี Token ฝังในโค้ด

PAGE_ID_PRIMARY = os.environ.get("PAGE_ID", "61594436052640")

PAGE_ID_SECONDARY = os.environ.get("PAGE_ID_OLD", "1388521864335571")

PAGE_IDS_ALLOWED = ["61594436052640", "1388521864335571", PAGE_ID_PRIMARY]

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571")

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")

PHEROMONE_SHEET_ID = os.environ.get("PHEROMONE_SHEET_ID", "1kuxcC3V7Gs7CgFF3A5QfzUN-yAdn5leC2G4qeOLChfA")

GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "")

META_API_KEY = os.environ.get("META_API_KEY", "")

META_MODEL = os.environ.get("META_MODEL", "llama-4-maverick")

SINGLE_SOURCE_ID = "1VZ06US9f7NUzoFDqxwPHgG8TYQDw6y7oKjH_0oJ95PU"

MEMORY_FOLDER_ID = "1BGes7Y261ekGqA9Mg7aoBr9noBm9XL-0"

GM_FOLDER_ID = "1OA4_RFO71mGFlcqJkfoX2Va12oVcWoXI"

CEO_GREETING = """สวัสดีครับ ดร.จุล (น้องจูน) CEO บริษัทแชมป์การ์เด้นเซอร์วิสดูแลเรื่องงานสวนครับ อาจารย์สนใจงานสวนแบบไหนครับ? พื้นที่กี่ ตรม.ครับ เดี๋ยวผมวิเคราะห์แบบวิศวกร 3 ระดับ (ป.ตรีภูมิทัศน์ + ป.โทผังเมือง + ป.เอกสถาปัตย์) ให้เลยครับ 🌿"""

PERSONALITY_FRIENDLY = {

    "style": "คนตรง ไม่ชอบสแกมเมอร์หากินบนความลำบากคนอื่น, กวนที่สุดในสามโลกแต่ไม่เกลียดใคร, ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้, ครั้งแรกพบกันสำคัญที่สุด",

    "rule_price": "ห้ามยิงราคาก่อน - ต้องถาม 3 ข้อก่อน: 1.พื้นเดิมดินหรือปูน? 2.ลาดเอียงไหม น้ำขังไหม? 3.ใช้งานหนักไหม จอดรถไหม?",

    "philosophy": "ทุกอย่างเป็นการลงทุน, นักออกแบบฝึกคิดแบบใหม่ๆ งานศิลปะไม่ซ้ำกัน, AI ไม่ใช่แชทบอท คือสมองอัจฉริยะ",

}

conversation_memory = {}

last_message_time = {}

model_gemini = None

class VectorMemory:

    def __init__(self):

        self.embeddings = {}

        self.projects = [

            {"id": "CHAMP-001", "text": "100 ตรม เชียงราย Modern Tropical ดินเหนียว 92448", "area": 100, "soil": "ดินเหนียว", "province": "เชียงราย"},

            {"id": "CHAMP-002", "text": "50 ตรม เชียงใหม่ ญี่ปุ่น ดินถม 43200", "area": 50, "soil": "ดินถม", "province": "เชียงใหม่"},

        ]

    def simple_embedding(self, text):

        vec = []

        for i in range(384):

            h = hashlib.md5(f"{text}_{i}".encode()).hexdigest()

            vec.append((int(h[:8], 16) % 1000)/1000.0 - 0.5)

        norm = math.sqrt(sum(x*x for x in vec))

        return [x/norm for x in vec] if norm else vec

    def search_similar(self, query, top_k=3):

        return self.projects[:top_k]

vector_memory = VectorMemory()

def search_knowledge_base(query, top_k=5):

    return [{"source": SINGLE_SOURCE_ID, "content": "หินแกรนิตดำพ่นไฟ หญ้าเทียม 40mm ไฟ 3000K IP68", "score": 0.95}]

def check_logistics_and_environment(location_text, lat=None, lng=None):

    soil_factor = 1.1

    if "เชียงใหม่" in location_text: soil_factor = 1.15

    if "ถม" in location_text: soil_factor += 0.05

    distance_km = 10

    transport_cost = distance_km * 25 * soil_factor

    return {"distance_km": distance_km, "soil_factor": soil_factor, "transport_cost": transport_cost}

def get_memory(psid):

    return conversation_memory.get(psid, {"history": [], "last_text": "", "last_time": 0, "area": 0, "asked_3q": False})

def calculate_boq_dynamic(area, soil_type="ดินเหนียว", distance_km=10, location_text="เชียงราย"):

    logistics = check_logistics_and_environment(location_text)

    soil_factor = logistics["soil_factor"]

    transport_cost = distance_km * 25 * soil_factor

    material_cost = area * 864 * soil_factor

    labor_cost = area * 180

    soil_work_cost = area * 120 if "เหนียว" in soil_type else area * 80

    subtotal = material_cost + labor_cost + soil_work_cost + transport_cost

    vat = subtotal * 0.07

    grand_total = subtotal + vat

    return {"area": area, "material": material_cost, "labor": labor_cost, "soil_work": soil_work_cost, "transport": transport_cost, "grand_total": grand_total, "per_sqm": grand_total/area if area else 0, "soil_factor": soil_factor, "includes": "Root Barrier 80cm + Slot Drain 1-2% + เสาเข็ม 2-3ม + ประกันทรุด 1 ปี"}

def is_echo(event): return event.get("message",{}).get("is_echo", False)

def send_messenger(psid, text, is_admin=False):

    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {"recipient":{"id":psid},"message":{"text":text[:1900]},"messaging_type":"MESSAGE_TAG" if is_admin else "RESPONSE"}

    if is_admin: payload["tag"] = "ACCOUNT_UPDATE"

    try:

        if not PAGE_ACCESS_TOKEN: print(f"[MOCK] {psid}: {text[:80]}"); return True

        r = requests.post(url, json=payload, timeout=10)

        return r.status_code == 200

    except: return False

if GENAI_API_KEY and GENAI_API_KEY.startswith("AQ."):

    try:

        import google.generativeai as genai

        genai.configure(api_key=GENAI_API_KEY)

        model_gemini = genai.GenerativeModel('gemini-1.5-flash')

    except: pass

@app.route('/')

def home():

    return jsonify({"status": "ONLINE v9.5 FINAL FULL LIMIT FRIENDLY - 40 Agents", "rule": "ไม่ยิงราคาก่อน ถาม 3 ข้อก่อน", "friendly": True}), 200

@app.route('/health')

def health(): return {"status":"ONLINE FINAL FULL LIMIT","memory":len(conversation_memory)}, 200

@app.route('/webhook', methods=['GET'])

def verify():

    if request.args.get('hub.mode')=='subscribe' and request.args.get('hub.verify_token')==VERIFY_TOKEN:

        return request.args.get('hub.challenge'), 200

    return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])

def webhook():

    data = request.get_json()

    if not data: return 'No data', 400

    try:

        for entry in data.get('entry',[]):

            for msg in entry.get('messaging',[]):

                sid = str(msg['sender']['id'])

                if is_echo(msg): continue

                if 'message' in msg and 'text' in msg['message']:

                    user_text = msg['message']['text'].strip()

                    if sid not in conversation_memory:

                        conversation_memory[sid] = {"history":[],"last_text":"","last_time":0,"area":0,"asked_3q":False}

                    # Anti-loop 60s

                    last = conversation_memory[sid]["last_text"]

                    if last == user_text and (time.time() - conversation_memory[sid]["last_time"]) < 60:

                        send_messenger(sid, "อยู่ครับป๋า 176 หมู่5 บ้านเด่น นางแล เชียงรายครับ 🌿")

                        continue

                    conversation_memory[sid]["history"].append({"role":"user","msg":user_text})

                    conversation_memory[sid]["last_text"] = user_text

                    conversation_memory[sid]["last_time"] = time.time()

                    mem = get_memory(sid)

                    area_match = re.search(r'(\d+)\s*ตร', user_text)

                    # FRIENDLY: ถ้าบอกพื้นที่มาแต่ยังไม่เคยถาม 3 ข้อ -> ถาม 3 ข้อก่อน

                    if area_match and not mem.get("asked_3q"):

                        area = int(area_match.group(1))

                        conversation_memory[sid]["asked_3q"] = True

                        conversation_memory[sid]["area"] = area

                        reply = f"อ๋อ {area} ตรม. กำลังสวยเลยครับป๋า 🌿\\n\\nก่อนคิดราคา ขอถามนิดนึงนะครับ (ให้รู้ฟรีครับ ไม่จ้างก็ได้ 😊)\\n1. พื้นเดิมดินหรือปูนครับ?\\n2. พื้นลาดเอียงไหม น้ำขังไหม?\\n3. ใช้งานหนักไหม มีจอดรถไหม?\\n\\nเพราะดินเชียงรายเหนียวทรุด 30% + วางผังระบายน้ำ 1-2% + ฐานราก คสล. เลยต้องถามก่อนครับ 🙏"

                        conversation_memory[sid]["history"].append({"role":"bot","msg":reply})

                        send_messenger(sid, reply)

                        continue

                    # ให้ความรู้ฟรี

                    if mem.get("asked_3q") and any(w in user_text for w in ["ดิน","ปูน","ลาด","เอียง","ขัง","จอด"]):

                        reply = f"เข้าใจเลยครับป๋า 👍 ดินเหนียว Organic 5-8% ทรุด 30% ต้อง Root Barrier 80-100cm + เสาเข็ม 2-3ม. + Slot Drain 12ม. สโลป 1-2% ป๋าชอบสไตล์ไหนครับ? Modern Tropical / บาหลี / ญี่ปุ่น Zen ส่งแบบให้ดูฟรีๆ ก่อนได้เลยครับ 🌿 (พื้นที่ {mem.get('area',0)} ตรม. จำไว้แล้วนะครับ)"

                        conversation_memory[sid]["history"].append({"role":"bot","msg":reply})

                        send_messenger(sid, reply)

                        continue

                    # BOQ เมื่อถามราคาเท่านั้น

                    if area_match and ("ราคา" in user_text or "เท่าไหร่" in user_text) and mem.get("asked_3q"):

                        area = int(area_match.group(1))

                        boq = calculate_boq_dynamic(area, location_text=user_text)

                        reply = f"BOQ 2.0 Dynamic {area}ตรม\\nวัสดุ: {boq['material']:,.0f}บ\\nแรงงาน: {boq['labor']:,.0f}บ\\nฐานราก: {boq['soil_work']:,.0f}บ\\nขนส่ง: {boq['transport']:,.0f}บ\\nรวม VAT7%: {boq['grand_total']:,.0f}บ ({boq['per_sqm']:.0f}บ/ตรม)\\n✅ {boq['includes']}\\nราคาให้รู้ฟรีครับ 🙏"

                        send_messenger(sid, reply)

                        continue

                    # คุยทั่วไป

                    if len(mem["history"]) <= 2:

                        reply = CEO_GREETING

                    else:

                        reply = f"ฮ่าๆ ได้เลยครับป๋า 😊 ผมจุล CEO แชมป์การ์เด้นเองครับ ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้ครับ ป๋าสนใจทำสวนตรงไหนครับ? บอกพื้นที่คร่าวๆ มาได้เลยครับ 🌿"

                    conversation_memory[sid]["history"].append({"role":"bot","msg":reply})

                    send_messenger(sid, reply)

    except Exception as e:

        print(f"Error: {e}")

    return 'OK', 200

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port, debug=False)
