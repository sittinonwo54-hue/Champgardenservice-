from flask import Flask, request
import os

app = Flask(__name__)
# ดึงรหัสลับจากตี้เฮาตั้งค่าไว้ใน Render
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # เฟซบุ๊กจะยิง GET มาเพื่อตรวจสอบยืนยัน Webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Forbidden', 403
        
    elif request.method == 'POST':
        # ส่วนนี้เอาไว้ฮับข้อความแชทลูกค้าในอนาคตครับ
        return 'EVENT_RECEIVED', 200

@app.route('/', methods=['GET'])
def home():
    return "Nong Jun AI is Running!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
