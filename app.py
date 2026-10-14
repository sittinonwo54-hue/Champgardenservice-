from flask import Flask, request, jsonify
import os, time, requests

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "champ_garden_verify_2026")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
memory = {}

@app.route('/')
def home():
    return jsonify({"status": "ONLINE SIMPLE", "message": "เซิร์ฟไม่หลับแล้วครับป๋า"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "OK"}), 200

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
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
            text = ev.get('message', {}).get('text', '')
            if sender and text:
                send_message(sender, f"รับทราบครับป๋า: {text} 🌿")
    return 'OK', 200

def send_message(psid, text):
    if not PAGE_ACCESS_TOKEN: return True
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json={"recipient":{"id":psid},"message":{"text":text[:1900]}})
    return True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
