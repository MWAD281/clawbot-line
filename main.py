from fastapi import FastAPI, Request, Header, HTTPException
import hashlib
import hmac
import base64
import os
import requests

app = FastAPI()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

@app.get("/")
def root():
    return {"status": "ClawBot is running"}

@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    body = await request.body()

    # Verify signature
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
            user_message = event["message"]["text"]

            reply_message(
                reply_token,
                f"ClawBot พร้อมใช้งานแล้ว 🤖\nคุณพิมพ์ว่า: {user_message}"
            )

    return {"ok": True}

def reply_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }
    requests.post(url, headers=headers, json=payload)
