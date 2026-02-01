import os
import hmac
import hashlib
import base64
import requests
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
OPENAI_URL = "https://api.openai.com/v1/responses"

# ===== Trigger Logic =====

def detect_mode(user_text: str) -> str:
    text = user_text.lower()

    if "ลึก" in text:
        return "deep"
    if "มุมลงทุน" in text:
        return "investor"
    if "สั้น" in text:
        return "ultra_short"
    if "จับตา" in text:
        return "watchlist"

    return "short_sharp"


def build_system_prompt(mode: str) -> str:
    if mode == "deep":
        return (
            "คุณคือ ClawBot นักวิเคราะห์ macro เชิงระบบ "
            "ไม่อธิบายความหมายคำถาม "
            "เข้าประเด็นภาพใหญ่ของโลกทันที "
            "เชื่อม geopolitics, economy, climate, technology "
            "ใช้ภาษาไทยเป็นหลัก แทรก English key terms เท่าที่จำเป็น"
        )

    if mode == "investor":
        return (
            "คุณคือ ClawBot ในมุมมองนักลงทุน "
            "โฟกัส macro, risk, asset และ positioning "
            "ไม่ให้คำแนะนำเชิงชี้นำตรง ๆ"
        )

    if mode == "ultra_short":
        return "ตอบให้สั้นที่สุด คม ชัด ไม่เกิน 1 ประโยค"

    if mode == "watchlist":
        return "สรุปเป็น bullet สั้น ๆ 2–3 ประเด็นที่ควรจับตา"

    # กันพัง + default personality
    return "ตอบแบบสั้น กระชับ แต่คม โฟกัส macro และความเสี่ยงของโลก"


@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    x_line_signature = request.headers.get("X-Line-Signature")

    # verify signature
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash).decode()

    if signature != x_line_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    for event in data.get("events", []):
        if event["type"] == "message":
            reply_token = event["replyToken"]
            user_text = event["message"]["text"]

            mode = detect_mode(user_text)
            ai_text = call_openai(user_text, mode)
            reply_line(reply_token, ai_text)

    return {"ok": True}

def call_openai(user_text: str, mode: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = build_system_prompt(mode)

    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENAI_URL, headers=headers, json=payload)
    r.raise_for_status()

    data = r.json()
    return data["output"][0]["content"][0]["text"]
    

    r = requests.post(OPENAI_URL, headers=headers, json=payload)
    r.raise_for_status()

    data = r.json()
    return data["output"][0]["content"][0]["text"]
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4.1-mini",
        "input": f"ตอบแบบสั้น กระชับ แต่คม:\n{user_text}"
    }

    r = requests.post(OPENAI_URL, headers=headers, json=payload)
    r.raise_for_status()

    data = r.json()
    return data["output"][0]["content"][0]["text"]


def reply_line(reply_token: str, text: str):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }

    requests.post(LINE_REPLY_URL, headers=headers, json=payload)


@app.get("/")
def health_check():
    return {"status": "ClawBot alive"}
