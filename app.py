# CHAMP GARDEN v10 LIVE HUMAN - LIVE สด ไม่เอาบอท
# พิมพ์ว่า live / แอดมิน / คุยกับคนจริง บอทจะหยุดทันที ให้คนจริงคุยต่อ

from flask import Flask, request, jsonify
import os, time, re, requests
from datetime import datetime

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571")

conversation_memory = {}
human_takeover = {} # ใครขอ LIVE สด บอทจะหยุด

def send_messenger(psid, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}}
    try:
        if not PAGE_ACCESS_TOKEN: print(f"[MOCK] {text[:100]}"); return True
        requests.post(url, json=payload, timeout=10)
        return True
    except: return False

def notify_admin(user_psid, user_text):
    try:
        if ADMIN_PSID:
            msg = f"🔴 LIVE REQUEST จาก {user_psid}\nพูดว่า: {user_text}\n\nบอทหยุดตอบคนนี้แล้ว 2 ชม. ให้ป๋าเข้าไปตอบใน Inbox เพจ CHAMP GARDEN SERVICE ได้เลยครับ\n\nพิมพ์ 'bot on {user_psid}' เพื่อให้บอทกลับมาทำงาน"
            send_messenger(ADMIN_PSID, msg)
    except: pass

@app.route('/')
def home():
    live_count = len([k for k,v in human_takeover.items() if v > time.time()])
    return jsonify({"status": "LIVE HUMAN READY - ไม่ใช่บอท", "live_chats": live_count, "total": len(conversation_memory)}), 200

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
                text = ev['message']['text'].strip()
                if not text: continue

                if sid not in conversation_memory:
                    conversation_memory[sid] = {"history": []}

                # ADMIN สั่งเปิด/ปิดบอท
                if sid == ADMIN_PSID and text.startswith("bot on"):
                    target = text.split()[-1] if len(text.split())>2 else ""
                    if target in human_takeover:
                        del human_takeover[target]
                        send_messenger(sid, f"เปิดบอทให้ {target} แล้วครับ")
                    else:
                        human_takeover.clear()
                        send_messenger(sid, "เปิดบอทให้ทุกคนแล้วครับ LIVE OFF")
                    continue
                if sid == ADMIN_PSID and text.startswith("bot off"):
                    target = text.split()[-1] if len(text.split())>2 else ""
                    if target:
                        human_takeover[target] = time.time() + 7200
                        send_messenger(sid, f"ปิดบอทให้ {target} 2 ชม. LIVE ON")
                    continue

                # ถ้าคนนี้อยู่ในโหมด LIVE สด - บอทจะไม่ตอบ ให้คนจริงตอบใน Inbox
                if sid in human_takeover and human_takeover[sid] > time.time():
                    print(f"[LIVE MODE] {sid} human takeover - bot silent")
                    continue
                elif sid in human_takeover and human_takeover[sid] <= time.time():
                    del human_takeover[sid] # หมดเวลา กลับมาเป็นบอท

                # ตรวจคำขอ LIVE สด
                live_keywords = ["live", "ไลฟ์", "สด", "คนจริง", "แอดมิน", "admin", "คุยกับคน", "คนตอบ", "พนักงาน", "เจ้าหน้าที่", "ต้องการlive"]
                if any(k in text.lower() for k in live_keywords):
                    human_takeover[sid] = time.time() + 7200 # หยุดบอท 2 ชม.
                    notify_admin(sid, text)
                    reply = """ได้เลยครับป๋า 🙏

เดี๋ยวผมให้แอดมินคนจริงมาคุยต่อนะครับ บอทหยุดตอบแล้ว 2 ชม.

ป๋ารอในแชทนี้ได้เลยครับ เดี๋ยวมีคนจริงมาตอบ LIVE สดๆ เลย

ถ้าอยากให้บอทกลับมา พิมพ์ว่า 'bot' ครับ 🌿"""
                    send_messenger(sid, reply)
                    conversation_memory[sid]["history"].append(text)
                    continue

                # ถ้าไม่ใช่ LIVE คุยเหมือนคนปกติ แต่ไม่ยิงราคา
                conversation_memory[sid]["history"].append(text)

                # คุยเหมือนคน ไม่ใช่บอทแข็งๆ
                if len(conversation_memory[sid]["history"]) == 1:
                    reply = """สวัสดีครับ ผมจุล CEO แชมป์การ์เด้นครับ 🌿

ตอนนี้มีทั้งบอทและคนจริงนะครับ ถ้าอยากคุยกับคนจริงพิมพ์ว่า 'live' ได้เลย

ป๋าสนใจทำสวนกี่ ตรม.ครับ?"""
                else:
                    area_match = re.search(r'(\d+)\s*ตร', text)
                    if area_match and "ราคา" not in text:
                        area = area_match.group(1)
                        reply = f"อ๋อ {area} ตรม กำลังดีเลยครับป๋า 🌿 พื้นเป็นดินหรือปูนครับ? มีน้ำขังไหมครับ? ถามไว้กันทรุดครับ ให้รู้ฟรีครับ"
                    else:
                        reply = f"รับทราบครับป๋า '{text}' 🌿 ผมจำได้แล้วครับ ถ้าอยากให้คนจริงมาตอบ LIVE สดๆ พิมพ์ว่า live ได้เลยนะครับ"

                send_messenger(sid, reply)
                conversation_memory[sid]["history"].append(reply)

    except Exception as e:
        print(f"Error {e}")
    return 'OK', 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
