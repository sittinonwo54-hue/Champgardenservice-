# app.py - v12.3 AUTO-POST ENABLED - 15OCT2026 - ระบบโพสเอง
from flask import Flask, request, jsonify
import os, time, requests, re

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
PAGE_ID = os.environ.get("PAGE_ID", "61594436052640")

memory = {}

DEFAULT_TEST_POST = """หวัดดีครับอ้าย 🙏

18 ปี 350+ โครงการ ไม่ได้โม้ครับอ้าย ดูผลงานจริงได้เลยครับ

ทำมาแล้วทั่วเชียงราย-เชียงใหม่ ดินแบบไหนเราก็เอาอยู่
ดินเหนียวทรุด 30%? เรามี Root Barrier 80cm + เสาเข็ม 2-3ม + Slot Drain 1-2% + ประกันทรุด 1 ปี

ทีม 5 คน พร้อมลุยครับ 💪
ให้รู้ฟรี ไม่จ้างก็ได้ครับ

📍 176 หมู่ 5 บ้านเด่น ต.นางแล อ.เมือง จ.เชียงราย
📞 064-0144865 | 095-1389002

#จัดสวนเชียงราย #CHAMPGARDEN"""

@app.route('/')
def home():
    return jsonify({"status": "ONLINE v12.3 AUTO-POST ENABLED", "auto_post": "GET /api/post-now", "page_id": PAGE_ID}), 200

@app.route('/health')
def health(): return jsonify({"status": "OK", "auto_post": True}), 200

@app.route('/ping')
def ping(): return "pong", 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return 'OK', 200
    for entry in data.get('entry', []):
        for ev in entry.get('messaging', []):
            if ev.get('message', {}).get('is_echo'): continue
            sender = ev.get('sender', {}).get('id')
            if not sender: continue
            text = ev.get('message', {}).get('text','')
            if memory.get(sender, {}).get('text') == text and time.time() - memory.get(sender, {}).get('time',0) < 60: continue
            memory[sender] = {"text": text, "time": time.time()}
            send_message(sender, f"รับทราบครับ: {text} 🌿")
    return 'OK', 200

def send_message(psid, text):
    if not PAGE_ACCESS_TOKEN: return True
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try: requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}}, timeout=10)
    except: pass
    return True

@app.route('/api/post-now', methods=['GET','POST'])
def post_now():
    msg = request.args.get('message')
    if not msg:
        try: msg = (request.get_json(silent=True) or {}).get('message')
        except: msg = None
    if not msg: msg = DEFAULT_TEST_POST
    if not PAGE_ACCESS_TOKEN:
        return jsonify({"error":"PAGE_ACCESS_TOKEN not set"}), 500
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
    r = requests.post(url, data={"message": msg, "access_token": PAGE_ACCESS_TOKEN}, timeout=15)
    result = r.json()
    if r.status_code == 200 and 'id' in result:
        return jsonify({"status":"SUCCESS","message":"โพสแล้วครับป๋า ระบบโพสเอง ✅","post_id": result['id'], "url": f"https://facebook.com/{result['id']}"}), 200
    return jsonify({"status":"FAILED","error": result}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8080)))
