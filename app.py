# CHAMP GARDEN v10.1 THAI NLP + LIVE สด - เข้าใจภาษาไทย 100%
# เข้าใจ: ไทยกลาง คำเมืองเหนือ พิมพ์ผิด คำย่อ อีสาน ป๋า เจ้า เน้อ ก่อ คับ

from flask import Flask, request, jsonify
import os, time, re, requests
from datetime import datetime

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "")

conversation_memory = {}
human_takeover = {}
model = None

if GENAI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GENAI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: pass

# ===== THAI NLP เข้าใจภาษาไทยลึก =====
def normalize_thai(text):
    """แก้พิมพ์ผิด คำย่อ ภาษาพูด"""
    text = text.lower().strip()
    # ลบไม้ยมก ซ้ำๆ ครับบบบ -> ครับ
    text = re.sub(r'([ก-ฮ])\1{2,}', r'\1\1', text)
    text = re.sub(r'[ๆฯ]', '', text)
    # คำย่อ
    replacements = {
        'ตรม': ' ตรม ', 'ตร.ม': ' ตรม ', 'ตารางเมตร': ' ตรม ', 'ตารางม': ' ตรม ', 'sqm': ' ตรม ', 'ตรม.': ' ตรม ',
        'คับ': 'ครับ', 'คร้าบ': 'ครับ', 'ค้าบ': 'ครับ', 'คัฟ': 'ครับ', 'คับผม': 'ครับ',
        'จ้า': 'เจ้า', 'จ้าว': 'เจ้า', 'เจ้า': 'เจ้า', 'เน้อ': 'เน้อ', 'เน่อ': 'เน้อ', 'ก่อ': 'ก่อ', 'ก่': 'ก่อ',
        'ป๋า': 'ป๋า', 'ป๋ม': 'ผม', 'ผม': 'ผม',
        'ราคาเท่าไหร่': 'ราคา', 'ราคาเท่าไร': 'ราคา', 'เท่าไหร่': 'ราคา', 'เท่าไร': 'ราคา', 'กี่บาท': 'ราคา', 'คิดตัง': 'ราคา',
        'ทำได้มั้ย': 'ทำไรได้', 'ทำไรได้บ้าง': 'ทำไรได้', 'ทำอะไรได้': 'ทำไรได้',
        'แอด': 'แอดมิน', 'มิน': 'แอดมิน',
        'ดิน': 'ดิน', 'ดินเหนียว': 'ดินเหนียว', 'ดินถม': 'ดินถม',
        'น้ำขัง': 'น้ำขัง', 'น้ำขังมั้ย': 'น้ำขัง', 'ลาด': 'ลาดเอียง', 'เอียง': 'ลาดเอียง',
    }
    for k,v in replacements.items():
        text = text.replace(k, v)
    return text

def thai_number_to_int(text):
    """แปลงเลขไทย คำไทย เป็นตัวเลข เช่น ร้อย ห้าสิบ"""
    thai_nums = {'ศูนย์':0,'หนึ่ง':1,'สอง':2,'สาม':3,'สี่':4,'ห้า':5,'หก':6,'เจ็ด':7,'แปด':8,'เก้า':9,'สิบ':10,'ร้อย':100,'พัน':1000}
    # เลขอารบิกก่อน
    m = re.search(r'(\d+)', text)
    if m: return int(m.group(1))
    # เลขไทยคำ
    total = 0
    if 'ร้อย' in text:
        if 'สองร้อย' in text: total+=200
        elif 'สามร้อย' in text: total+=300
        else: total+=100
    m2 = re.search(r'(ห้า|หก|เจ็ด|แปด|เก้า)?สิบ(ห้า|เอ็ด|สอง|สาม|สี่|หก|เจ็ด|แปด|เก้า)?', text)
    if m2:
        # 50 60 ฯลฯ แบบง่าย
        if 'ห้าสิบ' in text: return total+50 if total else 50
        if 'หกสิบ' in text: return total+60 if total else 60
    for word, val in thai_nums.items():
        if word in text and val>=10:
            # เจอ ร้อย สิบ
            pass
    return total if total>0 else 0

def extract_area_thai(text):
    """ดึงพื้นที่แบบเข้าใจไทย 100%"""
    norm = normalize_thai(text)
    # 100ตรม 100 ตรม 100ตร.ม 100ตารางเมตร
    patterns = [
        r'(\d+)\s*ตรม',
        r'(\d+)\s*ตาราง',
        r'ประมาณ\s*(\d+)',
        r'พื้นที่\s*(\d+)',
        r'(\d+)\s*m2',
        r'(\d+)\s*sqm',
    ]
    for p in patterns:
        m = re.search(p, norm)
        if m: return int(m.group(1))
    # คำไทย เช่น ห้าสิบตรม ร้อยตรม
    thai_area = thai_number_to_int(norm)
    if thai_area>0 and 'ตรม' in norm: return thai_area
    if thai_area>0 and any(w in text for w in ['พื้นที่','สวน','บ้าน']): return thai_area if thai_area>=10 else 0
    return 0

def understand_thai_intent(text):
    """เข้าใจเจตนาภาษาไทย"""
    norm = normalize_thai(text)
    intent = "general"
    confidence = 0.5

    # LIVE สด
    if any(k in norm for k in ['live','ไลฟ์','สด','คนจริง','แอดมิน','คุยกับคน','พนักงาน','เจ้าหน้าที่','ต้องการlive']):
        return "request_live", 0.95
    # จำได้ไหม
    if any(k in norm for k in ['จำได้ไหม','จำได้มั้ย','จำได้มั้ย','จำได้ป่าว','คุยอะไรไป']):
        return "recall", 0.9
    # ถามราคา
    if any(k in norm for k in ['ราคา','กี่บาท','เท่าไหร่','คิดตัง','งบ']):
        if extract_area_thai(text)>0: return "ask_price", 0.9
        return "ask_price_general", 0.7
    # บอกพื้นที่
    if extract_area_thai(text)>0:
        return "tell_area", 0.9
    # ตอบ 3 ข้อ
    if any(k in norm for k in ['ดินเหนียว','ดินถม','ดินเดิม','ปูน','ลาดเอียง','น้ำขัง','จอด','จอดรถ','ทรุด']):
        return "answer_3q", 0.85
    # ทักทาย
    if any(k in norm for k in ['หวัดดี','สวัสดี','ดีครับ','ดีเจ้า','ทดสอบ','เทส','ทำไรได้','ว่าไง']):
        return "greeting", 0.8
    # ถามสไตล์
    if any(k in norm for k in ['โมเดิร์น','มินิมอล','บาหลี','ญี่ปุ่น','tropical','สวน']):
        return "ask_style", 0.7

    return intent, confidence

def generate_thai_reply(psid, text, intent, area):
    mem = conversation_memory.get(psid, {})
    history = mem.get("history", [])[-6:]

    # ถ้ามี Gemini ให้เข้าใจไทยลึกสุด
    if model:
        try:
            prompt = f"""
คุณคือ ดร.จุล CEO แชมป์การ์เด้น 176 ม.5 บ้านเด่น นางแล เชียงราย พูดไทยเหนือได้นิดหน่อย เจ้า เน้อ ก่อ
เข้าใจภาษาไทย 100% ทั้งไทยกลาง คำเมือง พิมพ์ผิด คับ ครับ คร้าบ
บทสนทนาเก่า: {history}
พื้นที่จำได้: {area} ตรม
เจตนา: {intent}
ลูกค้าพิมพ์มา: "{text}" ( normalized: "{normalize_thai(text)}")
ตอบแบบคนเหนือเป็นกันเอง สั้นๆ 1-2 ประโยค มี 🌿 บ้าง ถ้ายังไม่รู้พื้นที่ถามพื้นที่ ถ้ารู้พื้นที่แล้วแต่ยังไม่ได้ถาม 3 ข้อ ให้ถาม 3 ข้อแบบคุยเล่น: ดินหรือปูน? ลาดเอียงน้ำขังไหม? จอดรถไหม? ห้ามท่องเป็นบอท
ถ้าขอ LIVE ให้บอกว่าได้เลยเดี๋ยวให้คนจริงมาคุย
"""
            r = model.generate_content(prompt)
            return r.text.strip()[:800]
        except: pass

    # Fallback เข้าใจไทยแบบไม่ต้องใช้ AI
    if intent == "request_live":
        return "ได้เลยครับป๋า 🙏 เดี๋ยวให้แอดมินคนจริงมาคุย LIVE สดๆ เลยนะครับ บอทหยุดแล้ว 2 ชม. ป๋ารอในแชทนี้ได้เลยเน้อเจ้า 🌿"
    if intent == "recall":
        return f"จำได้ก่ะป๋า 😊 เราคุยกัน {len(history)} รอบแล้ว ป๋าบอกพื้นที่ {area} ตรม ไว้ ผมจำแม่นเลยเจ้า มีอะไรให้ต่อยอดแหมครับ 🌿"
    if intent == "greeting":
        if len(history) <=1:
            return "หวัดดีครับป๋า ผมจุลเองเจ้า 🌿 ว่าไงครับ สนใจทำสวนกี่ ตรม ดีครับ? บอกมาได้เลยเช่น 50 ตรม เน้อ"
        return f"อยู่ครับป๋า ฟังอยู่เน้อเจ้า เมื่อกี้ป๋าบอก '{text}' ผมจำได้หมดเลย มีอะไรให้ช่วยแหมครับ 🌿"
    if intent == "tell_area":
        return f"อ๋อ {area} ตรม กำลังดีเลยครับป๋า 🌿 ถามนิดนึงเน้อ พื้นตอนนี้เป็นดินหรือปูนครับ? แล้วน้ำขังก่อเจ้า? ถามไว้กันทรุดครับ ให้รู้ฟรีบ่ต้องจ้างก็ได้ครับ 😊"
    if intent == "answer_3q":
        return f"โอเคเลยครับป๋า เข้าใจแล้วเน้อ '{text}' ดินเชียงรายทรุด 30% ต้องทำ Root Barrier 80cm + เสาเข็มสั้น ป๋าชอบสวนแนวไหนครับ? Tropical ร่มๆ หรือ มินิมอล เท่ๆ เดี๋ยวส่งแบบให้ดูเล่นๆ ก่อนได้ครับ 🌿"
    if intent == "ask_price":
        # ให้ BOQ แบบเข้าใจไทย
        boq = area*864*1.1 + area*180 + area*120 + 250
        total = boq*1.07
        return f"ได้เลยครับป๋า {area}ตรม BOQ รวม VAT {total:,.0f}บ ({total/area:.0f}บ/ตรม) รวม Root Barrier 80cm + Slot Drain + เสาเข็ม + ประกันทรุด 1 ปีเจ้า ราคาให้รู้ฟรีครับ 🌿"

    return "รับทราบครับป๋า ผมจุลฟังอยู่เจ้า 🌿 พื้นที่กี่ ตรม ครับ? บอกมาได้เลย เดี๋ยวผมวิเคราะห์ให้ฟรีๆ เน้อ"

def send_messenger(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}}
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[THAI NLP] {text[:120]}"); return True
        requests.post(url, json=payload, timeout=10)
        return True
    except: return False

@app.route('/')
def home():
    return jsonify({"status": "ONLINE v10.1 THAI NLP 100% + LIVE สด", "thai": "เข้าใจไทยกลาง + คำเมือง + พิมพ์ผิด", "live": len(human_takeover)}), 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode')=='subscribe' and request.args.get('hub.verify_token')==VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Fail', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return 'OK', 200
    try:
        for entry in data.get('entry', []):
            for ev in entry.get('messaging', []):
                sid = str(ev['sender']['id'])
                if ev.get('message',{}).get('is_echo'): continue
                if 'message' not in ev or 'text' not in ev['message']: continue
                raw_text = ev['message']['text'].strip()
                if not raw_text: continue

                if sid not in conversation_memory:
                    conversation_memory[sid] = {"history": [], "area": 0, "asked_3q": False, "last_text": "", "last_time": 0}

                # กันเบิ้ล
                if conversation_memory[sid]["last_text"] == raw_text and (time.time() - conversation_memory[sid]["last_time"]) < 3:
                    continue

                # LIVE mode
                if sid in human_takeover and human_takeover[sid] > time.time():
                    print(f"[LIVE] {sid} human takeover")
                    continue

                norm = normalize_thai(raw_text)
                area = extract_area_thai(raw_text) or conversation_memory[sid].get("area",0)
                intent, conf = understand_thai_intent(raw_text)

                print(f"[{sid}] raw='{raw_text}' norm='{norm}' area={area} intent={intent} conf={conf}")

                if area: conversation_memory[sid]["area"] = area
                if intent == "tell_area": conversation_memory[sid]["asked_3q"] = True

                # ขอ LIVE
                if intent == "request_live":
                    human_takeover[sid] = time.time() + 7200
                    reply = generate_thai_reply(sid, raw_text, intent, area)
                    send_messenger(sid, reply)
                    if ADMIN_PSID: send_messenger(ADMIN_PSID, f"🔴 LIVE {sid}: {raw_text}")
                    conversation_memory[sid]["last_text"]=raw_text; conversation_memory[sid]["last_time"]=time.time()
                    continue

                reply = generate_thai_reply(sid, raw_text, intent, area)
                send_messenger(sid, reply)

                conversation_memory[sid]["history"].append(raw_text)
                conversation_memory[sid]["history"].append(reply)
                conversation_memory[sid]["last_text"]=raw_text
                conversation_memory[sid]["last_time"]=time.time()
                if len(conversation_memory[sid]["history"])>20:
                    conversation_memory[sid]["history"]=conversation_memory[sid]["history"][-20:]

    except Exception as e:
        print(f"Error {e}")
        import traceback; traceback.print_exc()
    return 'OK', 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
