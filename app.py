from flask import Flask, request, jsonify import os, time, requests, re

app = Flask(name)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026") PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "") PAGE_ID = os.environ.get("PAGE_ID", "61594436052640") ADMIN_PSID = os.environ.get("ADMIN_PSID", "1388521864335571") PHEROMONE_SHEET_ID = os.environ.get("PHEROMONE_SHEET_ID", "1kuxcC3V7Gs7CgFF3A5QfzUN-yAdn5leC2G4qeOLChfA")

memory = {}
===== TEST POST CONTENT - Day6 15 OCT =====
DEFAULT_TEST_POST = """หวัดดีครับอ้าย 🙏

18 ปี 350+ โครงการ ไม่ได้โม้ครับอ้าย ดูผลงานจริงได้เลยครับ

ทำมาแล้วทั่วเชียงราย-เชียงใหม่ ดินแบบไหนเราก็เอาอยู่ ดินเหนียวทรุด 30%? เรามี Root Barrier 80cm + เสาเข็ม 2-3ม + Slot Drain 1-2% + ประกันทรุด 1 ปี

ทีม 5 คน พร้อมลุยครับ 💪 ให้รู้ฟรี ไม่จ้างก็ได้ครับ สนใจทักมาได้เลยครับ

📍 176 หมู่ 5 บ้านเด่น ต.นางแล อ.เมือง จ.เชียงราย 📞 064-0144865 | 095-1389002

#จัดสวนเชียงราย #จัดสวนเชียงใหม่ #CHAMPGARDEN"""

@app.route('/') def home(): return jsonify({ "status": "ONLINE v12.3 AUTO-POST ENABLED", "message": "ระบบโพสเองได้แล้วครับป๋า - ไม่ต้องโพสเอง", "page_id": PAGE_ID, "auto_post": "ready - GET /api/post-now เพื่อโพสทดสอบทันที", "agents": 40, "owner": "OWNER-001 พี่แชมป์", "time": time.time() }), 200

@app.route('/health') def health(): return jsonify({"status": "OK", "uptime": True, "auto_post": True}), 200

@app.route('/ping') def ping(): return "pong", 200

@app.route('/webhook', methods=['GET']) def verify(): mode = request.args.get('hub.mode') token = request.args.get('hub.verify_token') challenge = request.args.get('hub.challenge') if mode == 'subscribe' and token == VERIFY_TOKEN: return challenge, 200 return 'Verification failed', 403

@app.route('/webhook', methods=['POST']) def webhook(): data = request.get_json() if not data: return 'OK', 200 try: for entry in data.get('entry', []): for ev in entry.get('messaging', []): if ev.get('message', {}).get('is_echo'): continue sender = ev.get('sender', {}).get('id') if not sender or 'message' not in ev: continue text = ev['message'].get('text', '') if not text: continue if memory.get(sender, {}).get('text') == text and time.time() - memory.get(sender, {}).get('time', 0) < 60: continue memory[sender] = {"text": text, "time": time.time()} reply = f"รับทราบครับป๋า: {text} 🌿" if "ตรม" in text or "ตร.ม" in text: m = re.search(r'(\d+)', text) if m: area = int(m.group(1)) reply = f"{area} ตรม. รับทราบครับ เดี๋ยวคำนวณให้ครับ 🌿" send_message(sender, reply) except Exception as e: print(f"Error: {e}") return 'OK', 200

def send_message(psid, text): if not PAGE_ACCESS_TOKEN: print(f"[MOCK] {psid}: {text}") return True url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}" payload = {"recipient": {"id": psid}, "message": {"text": text[:1900]}} try: r = requests.post(url, json=payload, timeout=10) return r.status_code == 200 except: return False
===== AUTO-POST SYSTEM - ระบบโพสเอง =====
@app.route('/api/post-now', methods=['GET', 'POST']) def post_now(): """ยิงโพสลงเพจจริงทันที - สำหรับทดสอบ 1 โพส ตามคำสั่งป๋า""" # รับ message จาก query หรือ body ถ้าไม่มีใช้ DEFAULT msg = request.args.get('message') if not msg: try: body = request.get_json(silent=True) or {} msg = body.get('message') except: msg = None if not msg: msg = DEFAULT_TEST_POST

if not PAGE_ACCESS_TOKEN:

    return jsonify({"error": "PAGE_ACCESS_TOKEN not set in Render ENV", "status": "MOCK_POST", "message_preview": msg[:200]}), 500

url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"

data = {"message": msg, "access_token": PAGE_ACCESS_TOKEN}

try:

    r = requests.post(url, data=data, timeout=15)

    result = r.json()

    

    # บันทึกว่าโพสแล้ว (สำหรับ Pheromone)

    if r.status_code == 200 and 'id' in result:

        return jsonify({

            "status": "SUCCESS",

            "message": "โพสลงเพจจริงแล้วครับป๋า ✅ ระบบโพสเอง ไม่ต้องทำเอง",

            "post_id": result.get('id'),

            "page_id": PAGE_ID,

            "post_url": f"https://www.facebook.com/{result.get('id')}",

            "content_preview": msg[:150],

            "auto": True

        }), 200

    else:

        return jsonify({

            "status": "FAILED",

            "error": result,

            "page_id": PAGE_ID,

            "hint": "เช็ค PAGE_ACCESS_TOKEN หมดอายุไหม หรือ Page ID ถูกต้องไหม"

        }), 400

except Exception as e:

    return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/api/auto-post-daily', methods=['POST']) def auto_post_daily(): """สำหรับตั้ง Cron 19:00 ทุกวัน - ดึงจาก Content Calendar""" # ในอนาคตจะดึงจาก Google Sheet CONTENT_AUTO_POST # ตอนนี้ใช้ DEFAULT ไปก่อน แล้วอัพเกรดทีหลัง return post_now()

if name == 'main': port = int(os.environ.get("PORT", 8080)) app.run(host='0.0.0.0', port=port)
