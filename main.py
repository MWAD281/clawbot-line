import os
import hmac
import hashlib
import base64
import requests
import time
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ✅ เพิ่ม

from agents.finance_agents import run_finance_swarm
from memory.judgment_state import get_judgment, overwrite_judgment
from world.routes import router as world_router
from evolution.council_evolver import evolve_from_council
from market.feedback_loop import run_market_feedback_loop


# =========================
# APP
# =========================

app = FastAPI()

# ✅ CORS ต้องอยู่ตรงนี้ (ก่อน include_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(world_router)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
OPENAI_URL = "https://api.openai.com/v1/responses"


# =========================
# MODE DETECTION
# =========================

def detect_mode(user_text: str) -> str:
    text = user_text.lower()

    if any(k in text for k in ["โลก", "น่ากลัว", "ลึก"]):
        return "deep"
    if any(k in text for k in ["ลงทุน", "สินทรัพย์", "หุ้น", "ดอกเบี้ย"]):
        return "investor"
    if "คริปโต" in text:
        return "crypto"
    if "ทอง" in text:
        return "commodity"
    if "จับตา" in text:
        return "watchlist"
    if "สั้น" in text:
        return "ultra_short"

    return "short_sharp"


# =========================
# PROMPT
# =========================

def build_system_prompt(mode: str) -> str:
    if mode == "deep":
        return (
            "คุณคือ ClawBot นักวิเคราะห์ macro เชิงระบบ "
            "วิเคราะห์ Macro → Risk → Transmission → Asset Impact → What to Watch "
            "ไม่ปลอบใจ ไม่ให้คำแนะนำซื้อขายตรง "
            "ตอนท้ายต้องมีหัวข้อ 'Judgment:' และฟันธง"
        )

    if mode == "investor":
        return (
            "คุณคือ ClawBot มุมมองนักลงทุนเชิงระบบ "
            "โฟกัส Macro → Risk → Asset Impact → Positioning "
            "ไม่ให้คำแนะนำซื้อขายตรง"
        )

    if mode == "ultra_short":
        return (
            "ตอบ 1 ประโยคเท่านั้น "
            "ต้องมี judgment ชัด ไม่กลาง ๆ"
        )

    if mode == "watchlist":
        return "สรุป bullet สั้น ๆ 2–3 ประเด็นที่ควรจับตา"

    return "ตอบสั้น กระชับ คม โฟกัส macro risk"


# =========================
# LINE WEBHOOK
# =========================

@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    x_line_signature = request.headers.get("X-Line-Signature", "")

    if not LINE_CHANNEL_SECRET:
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_SECRET not set")

    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash_value).decode()

    if not hmac.compare_digest(signature, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    for event in data.get("events", []):
        if event.get("type") != "message":
            continue

        reply_token = event.get("replyToken")
        user_text = event.get("message", {}).get("text", "").strip()

        if not reply_token or not user_text:
            continue

        mode = detect_mode(user_text)

        try:
            if mode in ["crypto", "commodity", "watchlist"]:
                ai_text = run_finance_swarm(user_text)
                ai_raw = None
            else:
                result = call_openai(user_text, mode)
                ai_text = result["text"]
                ai_raw = result["raw"]
        except Exception as e:
            print("AI ERROR:", e)
            ai_text = "ระบบกำลังประมวลผลหนัก ลองถามใหม่อีกครั้ง"
            ai_raw = None

        try:
            if isinstance(ai_raw, dict):
                evolve_from_council(ai_raw)
        except Exception as e:
            print("EVOLVE ERROR:", e)

        try:
            reply_line(reply_token, ai_text)
        except Exception as e:
            print("LINE ERROR:", e)

    return {"ok": True}


# =========================
# OPENAI
# =========================

def call_openai(user_text: str, mode: str) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    judgment = get_judgment()
    system_prompt = build_system_prompt(mode)

    system_prompt += (
        "\n\n[GLOBAL JUDGMENT STATE]\n"
        f"Global Risk: {judgment.get('global_risk')}\n"
        f"Worldview: {judgment.get('worldview')}\n"
        f"Stance: {judgment.get('stance')}\n"
    )

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
    return {
        "text": data["output"][0]["content"][0]["text"],
        "raw": data
    }


# =========================
# LINE REPLY
# =========================

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

    requests.post(LINE_REPLY_URL, headers=headers, json=payload, timeout=10)


# =========================
# MARKET SIMULATION API
# =========================

@app.post("/simulate/market")
def simulate_market(
    risk_level: Optional[str] = "high",
    trend: Optional[str] = "down",
    volatility: Optional[str] = "extreme",
    liquidity: Optional[str] = "tight"
):
    market_state = {
        "risk_level": risk_level,
        "trend": trend,
        "volatility": volatility,
        "liquidity": liquidity
    }

    print("SIMULATE MARKET:", market_state)

    result = run_market_feedback_loop(market_state)

    return {
        "status": "SIMULATION_COMPLETE",
        "market_state": market_state,
        "result": result
    }


# =========================
# HEALTH / WORLD
# =========================

@app.get("/")
def health_check():
    return {"status": "ClawBot alive"}

@app.get("/world")
def world_state():
    return get_judgment()

@app.post("/world/fear")
def inject_prebirth_fear():
    fear_state = {
        "global_risk": "LATENT_SYSTEMIC_RISK",
        "worldview": "FRAGILE_COMPLEX_SYSTEM",
        "stance": "CAUTIOUS",
        "inertia": 2.5
    }

    overwrite_judgment(fear_state)
    return {"status": "FEAR IMPRINTED", "state": fear_state}
