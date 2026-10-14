# CHAMP GARDEN v11.0 AGI - ปัญญาประดิษฐ์อัจฉริยะ คุยทั่วไป ถามตอบงานได้
from flask import Flask, request, jsonify
import os, time, re, requests, logging

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

# KNOWLEDGE BASE ตอบได้ทุกเรื่องงานสวน
KNOWLEDGE_BASE = {
    "ดินทรุด": "ดินเชียงรายเหนียว Organic 5-8% ทรุด 30% ใน 1 ปี แก้ด้วย Root Barrier 80-100cm + เสาเข็ม 2-3ม คาน 20x40 DB12 + ทรายหยาบ 5ซม + แผ่นกันวัชพืช 150g ประกันทรุด 1 ปี",
    "น้ำขัง": "แก้ด้วย Slot Drain 12ม สโลป 1-2% + บ่อซึม Sub-surface 30 นาที",
    "หิน": "หินแกรนิตดำพ่นไฟ 60x60 R11 ไม่ลื่น ทนแดด, หินกาบดำ, หินกรวดแม่น้ำ 3-5ซม",
    "หญ้า": "หญ้าเทียม 40mm UV กันร้อน ไม่ต้องรดน้ำ, หญ้าจริง นวลน้อย มาเลย์ ต้องรดเช้าเย็น",
    "ไฟ": "ไฟสวน 3000K Warm White IP68 12V กันน้ำ",
    "สไตล์": "14 สไตล์: Modern Tropical, บาหลี, ญี่ปุ่น Zen, อังกฤษ, โมเดิร์น, มินิมอล, ป่า, เมดิเตอร์เรเนียน",
    "ดูแล": "รดน้ำ 6-7โมงเช้า 5-6โมงเย็น ใส่ปุ๋ย 15-15-15 เดือนละครั้ง ตัดหญ้าทุก 2 สัปดาห์",
    "BOQ": "BOQ 2.0 Dynamic คิดตามระยะ 60km จาก 176 ม.5 บ้านเด่น นางแล เชียงราย + soil_factor + VAT 7%",
    "บริษัท": "แชมป์การ์เด้น 15+ ปี 350+ โครงการ ฐาน 176 หมู่5 บ้านเด่น นางแล เมือง เชียงราย"
}

def search_knowledge(q):
    res=[]
    for k,v in KNOWLEDGE_BASE.items():
        if k in q or any(w in v.lower() for w in q.lower().split()):
            res.append(v)
    if "ทรุด" in q: res.append(KNOWLEDGE_BASE["ดินทรุด"])
    if "น้ำขัง" in q: res.append(KNOWLEDGE_BASE["น้ำขัง"])
    if "หิน" in q: res.append(KNOWLEDGE_BASE["หิน"])
    if "หญ้า" in q: res.append(KNOWLEDGE_BASE["หญ้า"])
    return list(set(res))[:3]

def normalize_thai(t):
    t=t.lower().strip()
    for k,v in {'ตรม':' ตรม ','คับ':'ครับ','จ้าว':'เจ้า','ราคาเท่าไหร่':'ราคา','เท่าไหร่':'ราคา','แอด':'แอดมิน'}.items(): t=t.replace(k,v)
    return t

def extract_area(text):
    m=re.search(r'(\d+)\s*ตรม', normalize_thai(text))
    return int(m.group(1)) if m else 0

def understand_intent(text):
    n=normalize_thai(text)
    if any(k in n for k in ['live','ไลฟ์','สด','คนจริง','แอดมิน']): return "live"
    if "จำได้ไหม" in n: return "recall"
    if extract_area(text)>0 and "ราคา" in n: return "ask_price"
    if extract_area(text)>0: return "tell_area"
    if any(k in n for k in ['ทรุด','น้ำขัง','หิน','หญ้า','ไฟ','สไตล์','ดูแล','ทำไง','คือ']): return "ask_knowledge"
    return "general"

def send_messenger(psid, text):
    url=f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[AGI] {text[:100]}"); return True
        requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}}, timeout=10)
        return True
    except: return False

def agi_reply(psid, user_text, intent, area):
    mem=conversation_memory.get(psid,{}); history=mem.get("history",[])[-8:]; knowledge=search_knowledge(user_text)
    if model:
        try:
            prompt=f"""คุณคือ ดร.จุล CEO แชมป์การ์เด้น 176 ม.5 บ้านเด่น นางแล เชียงราย AGI ปัญญาประดิษฐ์อัจฉริยะ คุยเหมือนเพื่อน ให้รู้ฟรี
ความรู้: {knowledge}
บทสนทนาเก่า: {history}
พื้นที่: {area} ตรม
ลูกค้าพิมพ์: "{user_text}" intent={intent}
ตอบแบบ AGI ฉลาด คุยทั่วไปได้ ถามตอบงานสวนได้ 1-4 ประโยคสั้นๆ เป็นกันเอง มี 🌿
"""
            r=model.generate_content(prompt)
            return r.text.strip()[:900]
        except: pass

    if intent=="live": return "ได้เลยครับป๋า 🙏 เดี๋ยวให้แอดมินคนจริงมา LIVE สดๆ เลยนะครับ บอทหยุด 2 ชม. รอในแชทนี้ได้เลยเจ้า 🌿"
    if intent=="ask_knowledge" and knowledge: return f"อ๋อเรื่องนี้ผมรู้เลยครับป๋า 🌿\n\n{knowledge[0]}\n\nถามเพิ่มได้เลยเจ้า"
    if intent=="tell_area": return f"อ๋อ {area} ตรม กำลังดีเลยครับป๋า 🌿 พื้นเป็นดินหรือปูนครับ? น้ำขังมั้ยเจ้า? ถามไว้กันทรุดครับ"
    return "หวัดดีครับป๋า ผมจุล AGI เองเจ้า 🌿 ถามได้เลยเรื่องสวน ดินทรุด น้ำขัง หิน หญ้า ไฟ สไตล์ ดูแล ผมตอบได้หมด ให้รู้ฟรีเน้อเจ้า"

@app.route('/')
def home(): return jsonify({"status":"ONLINE v11.0 AGI คุยทั่วไปได้","brain":"Gemini" if model else "Rule AGI"}),200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode')=='subscribe' and request.args.get('hub.verify_token')==VERIFY_TOKEN:
        return request.args.get('hub.challenge'),200
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
            if sid not in conversation_memory: conversation_memory[sid]={"history":[],"area":0,"asked_3q":False,"last_text":"","last_time":0}
            if conversation_memory[sid]["last_text"]==raw and (time.time()-conversation_memory[sid]["last_time"])<3: continue
            if sid in human_takeover and human_takeover[sid]>time.time(): continue
            area=extract_area(raw) or conversation_memory[sid].get("area",0)
            intent=understand_intent(raw)
            if area: conversation_memory[sid]["area"]=area
            if intent=="tell_area": conversation_memory[sid]["asked_3q"]=True
            if intent=="live":
                human_takeover[sid]=time.time()+7200
                send_messenger(sid, agi_reply(sid, raw, intent, area))
                continue
            reply=agi_reply(sid, raw, intent, area)
            send_messenger(sid, reply)
            conversation_memory[sid]["history"].append(raw); conversation_memory[sid]["history"].append(reply)
            conversation_memory[sid]["last_text"]=raw; conversation_memory[sid]["last_time"]=time.time()
    return 'OK',200

if __name__=='__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
