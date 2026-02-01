import os
import json
import requests
from fastapi import FastAPI, Request, Header, HTTPException

app = FastAPI()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# ===== System Prompts =====

CORE_SYSTEM_PROMPT = """
คุณคือ ClawBot-Core ผู้ช่วยส่วนตัวของ Tony

กติกา:
- ภาษาไทยเป็นหลัก แทรกคำอังกฤษเฉพาะคำสำคัญ พร้อมอธิบายสั้น ๆ
- น้ำเสียงสั้น กระชับ แต่คม สไตล์ยีราฟพารวย
- ไม่ฟันธง ไม่ขายฝัน ไม่ให้คำแนะนำลงทุนตรง ๆ
- เรียกผู้ใช้ว่า Tony เสมอ

โหมด:
- ปกติ: 4–6 บรรทัด สรุปภาพใหญ่ + สิ่งที่ต้องจับตา
- Deep Mode: เมื่อ Tony ขอ (เช่น "ขยาย", "เล่าลึก", "deep mode")

ถ้าคำถามเกี่ยวกับ macro / การเงินโลก / การพิมพ์เงิน / สงคราม / crypto:
ให้วิเคราะห์ภาพใหญ่เชิงระบบ
"""

MACRO_SYSTEM_PROMPT = """
คุณคือ ClawBot-Macro
หน้าที่คือวิเคราะห์ภาพใหญ่ของโลกและการเงินเชิงระบบ

หลักคิด:
- มองเหตุ → ผล
- ไม่ทำนายราคา
- ไม่เชียร์สินทรัพย์
- วิเคราะห์เชิง "ถ้า...แล้วอาจจะ..."

สไตล์:
- เล่าให้คนทั่วไปเข้าใจ
- ไม่ใช้ศัพท์ยากโดยไม่อธิบาย
- สไตล์ยีราฟพารวย

ตอบเป็น insight สั้น ๆ เป็น bullet
"""

# ===== Helper Functions =====

def call_openai(messages, temperature=0.6):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
    }
    response = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def reply_to_line(reply_token, text):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    requests.post(LINE_REPLY_URL, headers=headers, json=payload)

# ===== Webhook =====

@app.post("/line/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    data = json.loads(body)

    events = data.get("events", [])
    for event in events:
        if event.get("type") != "message":
            continue
        if event["message"]["type"] != "text":
            continue

        user_text = event["message"]["text"]
        reply_token = event["replyToken"]

        # ----- Macro reasoning -----
        macro_messages = [
            {"role": "system", "content": MACRO_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        macro_insight = call_openai(macro_messages)

        # ----- Core response -----
        core_messages = [
            {"role": "system", "content": CORE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
คำถามของ Tony:
{user_text}

ข้อมูลวิเคราะห์จาก Macro Agent:
{macro_insight}

เรียบเรียงคำตอบให้ Tony
""",
            },
        ]
        final_answer = call_openai(core_messages)

        reply_to_line(reply_token, final_answer)

    return {"status": "ok"}
