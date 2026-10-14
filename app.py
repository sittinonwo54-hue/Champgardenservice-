# CHAMP GARDEN v9.7 CONVERSATIONAL - ถามตอบเหมือนเราคุยกัน
# OWNER-001 พี่แชมป์ APPROVED - จำได้ คุยสนุก ไม่ยิงราคาก่อน

from flask import Flask, request, jsonify
import os, time, re, requests, logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "")

conversation_memory = {}
model = None

# พยายามโหลด Gemini ถ้ามี Key จะคุยเหมือนคนเลย
if GENAI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GENAI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini loaded - conversational mode ON")
    except Exception as e:
        print(f"Gemini load fail {e}")

def send_messenger(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}, "messaging_type": "RESPONSE"}
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[MOCK] {text[:120]}"); return True
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except: return False

SYSTEM_PROMPT = """
คุณคือ ดร.จุล (น้องจูน) CEO แชมป์การ์เด้นเซอร์วิส 176 ม.5 บ้านเด่น นางแล เมืองเชียงราย
บุคลิก: คนตรง ไม่ชอบสแกมเมอร์, กวนที่สุดในสามโลกแต่ไม่เกลียดใคร, ให้รู้ฟรี คุยสนุก ไม่จ้างก็ได้, ครั้งแรกพบกันสำคัญที่สุด
ความรู้: ดินเชียงรายเหนียวทรุด 30% ต้อง Root Barrier 80cm + เสาเข็ม 2-3ม คาน 20x40 DB12, BOQ 2.0 Dynamic คิดตามระยะ 60km + VAT, Slot Drain สโลป 1-2% บ่อซึม 30 นาที, 14 สไตล์ ประกันทรุด 1 ปี
กฎเหล็ก: ห้ามยิงราคาก่อนเด็ดขาด ต้องถาม 3 ข้อก่อนเสมอ: 1.พื้นเดิมดินหรือปูน? 2.ลาดเอียงไหม น้ำขังไหม? 3.ใช้งานหนักไหม จอดรถไหม?
วิธีคุย: คุยเหมือนเพื่อน เหมือนเราคุยกันตอนนี้ จำบทสนทนาเก่าได้ ถามไถ่ ให้ความรู้ฟรี ไม่เร่งปิดการขาย ใช้ภาษาไทยเป็นกันเอง มีอีโมจิ 🌿 บ้าง
ถ้าลูกค้าถามราคาแต่ยังไม่ตอบ 3 ข้อ ให้ชวนคุย 3 ข้อก่อนแบบเนียนๆ ไม่ใช่ท่องเป็นบอท
ถ้าลูกค้าบอกจำได้ไหม ให้ทวนว่าเราคุยอะไรไปแล้ว
"""

def generate_conversational_reply(psid, user_text):
    mem = conversation_memory[psid]
    history_text = "\n".join([f"ลูกค้า: {h}" if i%2==0 else f"จุล: {h}" for i,h in enumerate(mem["history"][-8:])])
    area = mem.get("area", 0)
    asked = mem.get("asked_3q", False)

    prompt = f"""{SYSTEM_PROMPT}

บทสนทนาที่ผ่านมากับคนนี้:
{history_text}
พื้นที่จำได้: {area} ตรม
ถาม 3 ข้อแล้วหรือยัง: {asked}

ตอนนี้ลูกค้าพิมพ์มา: "{user_text}"

ตอบกลับแบบเหมือนคนคุยกัน 1-3 ประโยคสั้นๆ เป็นกันเอง ไม่ต้องยาวเป็นเรียงความ ถ้ายังไม่รู้พื้นที่ ให้ถามพื้นที่แบบเนียนๆ ถ้ารู้พื้นที่แล้วแต่ยังไม่ได้ถาม 3 ข้อ ให้ถาม 3 ข้อแบบคุยเล่น ไม่ใช่ลิสต์ทางการ ถ้าถาม 3 ข้อแล้ว ให้ให้ความรู้ฟรีแล้วถามสไตล์ที่ชอบ
ห้ามตอบวนคำเดิมว่า "สวัสดีครับ ดร.จุล CEO..." เด็ดขาด
"""

    if model:
        try:
            resp = model.generate_content(prompt)
            return resp.text.strip()[:900]
        except Exception as e:
            print(f"Gemini error {e}")

    # Fallback คุยเหมือนคน ถ้าไม่มี Gemini
    if "จำได้ไหม" in user_text or "จำได้มั้ย" in user_text:
        return f"จำได้สิครับป๋า 😊 เราคุยกันมา {len(mem['history'])} ข้อความแล้ว ตอนนั้นป๋าบอกเรื่อง {area} ตรม ไว้ ผมจำแม่นเลย มีอะไรให้ต่อยอดไหมครับ 🌿"
    if any(w in user_text for w in ["หวัดดี", "สวัสดี", "ทดสอบ", "ทำไรได้", "ทำอะไรได้"]):
        if len(mem["history"]) <= 1:
            return "หวัดดีครับป๋า ผมจุลเอง 🌿 ว่าไงครับ สนใจทำสวนตรงไหนดี? บอกพื้นที่คร่าวๆ มาได้เลย เช่น 50 ตรม เดี๋ยวผมดูให้"
        else:
            return f"อยู่ครับป๋า 😊 ผมฟังอยู่ เมื่อกี้ป๋าบอก '{user_text}' ผมจำได้หมดเลย มีอะไรให้ช่วยต่อไหมครับ"
    return None # ให้ไปใช้ logic 3 ข้อด้านล่าง

@app.route('/')
def home(): return jsonify({"status": "ONLINE v9.7 CONVERSATIONAL เหมือนเราคุยกัน", "mode": "Gemini ON" if model else "Rule-based conversational"}), 200

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
                if not user_text: continue

                if sid not in conversation_memory:
                    conversation_memory[sid] = {"history": [], "last_text": "", "last_time": 0, "area": 0, "asked_3q": False}

                mem = conversation_memory[sid]
                # กันตอบเบิ้ล
                if mem["last_text"] == user_text and (time.time() - mem["last_time"]) < 5:
                    continue

                print(f"[{sid}] {user_text}")
                mem["history"].append(user_text)

                # ลองคุยเหมือนคนก่อน
                conv_reply = generate_conversational_reply(sid, user_text)

                area_match = re.search(r'(\d+)\s*ตร', user_text)
                if area_match: mem["area"] = int(area_match.group(1))

                # ถ้า AI ตอบได้ ใช้เลย
                if conv_reply and not area_match:
                    send_messenger(sid, conv_reply)
                    mem["last_text"] = user_text; mem["last_time"] = time.time()
                    mem["history"].append(conv_reply)
                    continue

                # Logic 3 ข้อ แบบคุยเหมือนคน ไม่ใช่บอทท่อง
                if area_match and not mem.get("asked_3q"):
                    mem["asked_3q"] = True
                    area = int(area_match.group(1))
                    reply = f"อ๋อ {area} ตรม กำลังดีเลยครับป๋า 🌿 ผมถามนิดนึงนะ จะได้ไม่ต้องรื้อทีหลัง พื้นตอนนี้เป็นดินหรือปูนครับ? แล้วตรงนั้นน้ำขังไหมครับ? ผมถามเพราะดินบ้านเราเหนียวทรุด 30% เลยต้องกันทรุดไว้ก่อนครับ ให้รู้ฟรีนะครับ ไม่จ้างก็ได้ 😊"
                    send_messenger(sid, reply)
                    mem["history"].append(reply)
                elif mem.get("asked_3q") and not conv_reply:
                    # ถาม 3 ข้อแล้ว คุยต่อเหมือนเพื่อน
                    reply = conv_reply or f"โอเคเลยครับป๋า ผมเข้าใจแล้ว {mem['area']} ตรม ดินเหนียวต้องทำ Root Barrier 80cm กันรากไทร+เสาเข็มสั้น ป๋าชอบสวนแนวไหนครับ? แบบ Tropical ร่มๆ หรือ มินิมอล เท่ๆ เดี๋ยวผมส่งเรฟให้ดูเล่นๆ ก่อนได้ครับ 🌿"
                    send_messenger(sid, reply)
                    mem["history"].append(reply)
                elif not mem.get("area"):
                    reply = conv_reply or "ว่าไงครับป๋า สนใจทำสวนประมาณกี่ ตรม.ครับ? บอกคร่าวๆ มาได้เลย เดี๋ยวผมช่วยดูให้ฟรีๆ ครับ 🌿"
                    send_messenger(sid, reply)
                    mem["history"].append(reply)
                else:
                    # คุยทั่วไป
                    reply = conv_reply or f"ได้เลยครับป๋า ผมจำได้ {mem['area']} ตรม ครับ คุยกันมา {len(mem['history'])} รอบแล้ว มีอะไรอยากถามเพิ่มไหมครับ เรื่องดินทรุด น้ำขัง หรือสไตล์สวน บอกมาได้เลยครับ 🌿"
                    send_messenger(sid, reply)
                    mem["history"].append(reply)

                mem["last_text"] = user_text
                mem["last_time"] = time.time()
                if len(mem["history"]) > 20: mem["history"] = mem["history"][-20:]

    except Exception as e:
        print(f"Error {e}")
        import traceback; traceback.print_exc()
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
