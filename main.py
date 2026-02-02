import os
import hmac
import hashlib
import base64
import requests
from fastapi import FastAPI, Request, HTTPException

from agents.investor_agents import run_investor_swarm
from agents.finance_agents import run_finance_swarm
from memory.judgment_state import get_judgment, update_judgment

app = FastAPI()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")


LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
OPENAI_URL = "https://api.openai.com/v1/responses"

# ===== Trigger Logic =====

def detect_mode(user_text: str) -> str:
    text = user_text.lower()

    # 🔥 คำถามเชิง abstract / ภาพโลก
    if "โลก" in text or "น่ากลัว" in text:
        return "deep"

    if "ลึก" in text:
        return "deep"
    if any(k in text for k in ["ลงทุน", "สินทรัพย์", "หุ้น", "ดอกเบี้ย"]):
        return "investor"
    if "คริปโต" in text:
        return "crypto"
    if "ทอง" in text or "commodity" in text:
        return "commodity"
    if "จับตา" in text:
        return "watchlist"
    if "สั้น" in text:
        return "ultra_short"

    return "short_sharp"

def build_system_prompt(mode: str) -> str:
    if mode == "deep":
        return (
            "คุณคือ ClawBot นักวิเคราะห์ macro เชิงระบบ "
            "คิดแบบนักลงทุนระยะยาว ไม่อธิบายความหมายคำถาม "
            "เข้าภาพใหญ่ของโลกทันที "
            "วิเคราะห์ตามลำดับ: Macro → Risk → Transmission → Asset Impact → What to Watch "
            "เชื่อม geopolitics, economy, liquidity, climate, technology "
            "ใช้ภาษาไทยเป็นหลัก แทรก English key terms ที่จำเป็นเท่านั้น "
            "ไม่ปลอบใจ ไม่ให้คำแนะนำซื้อขายตรง "
            "ตอนท้ายต้องมีหัวข้อชัดเจนว่า 'Judgment:' "
            "และสรุปโลกตอนนี้ด้วย 1–2 ประโยคแบบฟันธง ห้ามกลาง ๆ "
            "Judgment ต้องเลือก stance เดียว ห้ามมีคำว่า 'ทั้งนี้', 'อย่างไรก็ตาม', หรือ 'ขึ้นอยู่กับ'"
        )
        
    if mode == "investor":
        return (
            "คุณคือ ClawBot ในมุมมองนักลงทุนเชิงระบบ "
            "โฟกัส Macro → Risk → Asset Impact → Positioning "
            "ไม่ให้คำแนะนำซื้อขายตรง "
              "เน้น scenario, framework และสิ่งที่ต้องจับตา "
            "ใช้ภาษาไทยเป็นหลัก แทรก English key terms ที่จำเป็น"
        )

    if mode == "ultra_short":
        return (
             "ตอบ 1 ประโยคเท่านั้น "
            "ต้องมีมุมมองชัด (judgment) "
            "ไม่ใช้ภาษาปลอบใจ ไม่กลาง ๆ "
            "เน้น macro risk หรือ implication"
        )

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

    if not hmac.compare_digest(signature, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    for event in data.get("events", []):
        if event["type"] == "message":
            reply_token = event["replyToken"]
            user_text = event["message"]["text"]

            # Detect mode
            mode = detect_mode(user_text)

            # Call appropriate bot
            if mode == "investor":
                ai_text = run_investor_swarm(user_text)
            elif mode in ["crypto", "commodity", "watchlist"]:
                ai_text = run_finance_swarm(user_text)
            else:
                ai_text = call_openai(user_text, mode)

            # Reply back to LINE
            reply_line(reply_token, ai_text)

    return {"ok": True}

def call_openai(user_text: str, mode: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
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

    r = requests.post(
        OPENAI_URL,
        headers=headers,
        json=payload,
        timeout=20
    )
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

