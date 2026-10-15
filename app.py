import os, requests

GOOGLE_URL = os.getenv("GOOGLE_SCRIPT_URL")
CHAMP_KEY = "CHAMP-SECRET-KEY-2026-GLOBAL-60"

def call_champ_server(text):
    try:
        url = f"{GOOGLE_URL}?key={CHAMP_KEY}&action=global&text={text}"
        r = requests.get(url, timeout=15)
        data = r.json()
        return f"BOQ {data['boq']['grand_total']} บาท จาก {data['agents_count']} คน"
    except Exception as e:
        return f"เซิร์ฟ 60 คนกำลังบูท: {e}"

# ในตอนตอบแชท
if "ราคา" in user_text or "ตรม" in user_text:
    boq_info = call_champ_server(user_text)
    reply = f"{gemini_reply}\n\n{boq_info}"
