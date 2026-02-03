from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import time
import random
import uuid
import hashlib
import hmac
import base64

# =========================
# BASIC APP
# =========================
app = FastAPI(title="ClawBot Phase 35 – LINE Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")

LINE_REPLY_API = "https://api.line.me/v2/bot/message/reply"

# =========================
# SIMPLE BRAIN (Stub)
# ต่อ Darwinism ทีหลังได้
# =========================
def clawbot_brain(text: str) -> str:
    text = text.lower()

    if "สงคราม" in text:
        return "⚠️ ความเสี่ยงโลกสูงขึ้น ควรลด leverage และเพิ่มสินทรัพย์ปลอดภัย"

    if "ทดสอบ" in text:
        return "✅ ClawBot ONLINE พร้อมรบ"

    return "🧠 ClawBot รับข้อมูลแล้ว กำลังประเมินความเสี่ยงเชิงกลยุทธ์"

# =========================
# LINE SIGNATURE VERIFY
# =========================
def verify_signature(body: bytes, signature: str):
    hash = hmac.new(
        LINE_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash).decode()
    return hmac.compare_digest(expected, signature)

# =========================
# LINE WEBHOOK
# =========================
@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    body = await request.body()

    if not verify_signature(body, x_line_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    events = payload.get("events", [])

    async with httpx.AsyncClient(timeout=5) as client:
        for event in events:
            if event["type"] != "message":
                continue

            if event["message"]["type"] != "text":
                continue

            reply_token = event["replyToken"]
            user_text = event["message"]["text"]

            reply_text = clawbot_brain(user_text)

            await client.post(
                LINE_REPLY_API,
                headers={
                    "Authorization": f"Bearer {LINE_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "replyToken": reply_token,
                    "messages": [
                        {
                            "type": "text",
                            "text": reply_text
                        }
                    ]
                }
            )

    return {"status": "ok"}

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 35 ONLINE",
        "epoch": 0,
        "generation": 1,
        "pressure": 1.0,
        "deception": 0.0
    }
