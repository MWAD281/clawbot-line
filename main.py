import os
import hmac
import hashlib
import base64
import requests
from typing import Optional, Dict, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.finance_agents import run_finance_swarm
from memory.judgment_state import get_judgment, overwrite_judgment
from world.routes import router as world_router
from evolution.council_evolver import evolve_from_council
from market.feedback_loop import run_market_feedback_loop


# =========================
# APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(world_router)


# =========================
# ENV
# =========================

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
OPENAI_URL = "https://api.openai.com/v1/responses"


# =========================
# COUNCIL
# =========================

def council_vote(market_state: Dict) -> Dict:
    votes = []

    # Hawk – ระวังความเสี่ยง
    if market_state["risk_level"] == "high":
        votes.append("RISK_UP")

    # Dove – มองผ่อนคลาย
    if market_state["trend"] == "down" and market_state["liquidity"] != "tight":
        votes.append("STABLE")

    # Chaos – tail risk
    if market_state["volatility"] == "extreme":
        votes.append("CHAOS")

    # Historian – เทียบอดีต
    if market_state["trend"] == "down" and market_state["risk_level"] == "high":
        votes.append("CRISIS_PATTERN")

    # Survivor – โหมดเอาตัวรอด
    if market_state["liquidity"] == "tight":
        votes.append("DEFENSIVE")

    return {
        "votes": votes,
        "count": len(votes)
    }


def apply_council_to_judgment(judgment: Dict, council: Dict) -> Dict:
    new_judgment = judgment.copy()

    if "CHAOS" in council["votes"]:
        new_judgment["worldview"] = "fragile"
        new_judgment["confidence"] = min(1.0, judgment.get("confidence", 0.2) + 0.2)

    if council["count"] >= 3:
        new_judgment["stance"] = "DEFENSIVE"
        new_judgment["global_risk"] = "HIGH"

    return new_judgment


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
            "ตอนท้ายต้องมีหัวข้อ Judgment:"
        )

    if mode == "investor":
        return (
            "คุณคือ ClawBot มุมมองนักลงทุนเชิงระบบ "
            "โฟกัส Macro → Risk → Asset Impact"
        )

    if mode == "ultra_short":
        return "ตอบ 1 ประโยค judgment ชัดเจน"

    if mode == "watchlist":
        return "สรุป bullet สั้น ๆ 2–3 ประเด็น"

    return "ตอบสั้น กระชับ โฟกัส macro risk"


# =========================
# LINE WEBHOOK
# =========================

@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode(),
        body,
        hashlib.sha256
    ).digest()

    if base64.b64encode(hash_value).decode() != signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    for event in data.get("events", []):
        if event.get("type") != "message":
            continue

        reply_token = event["replyToken"]
        user_text = event["message"]["text"]

        mode = detect_mode(user_text)
        ai_text = run_finance_swarm(user_text)

        reply_line(reply_token, ai_text)

    return {"ok": True}


# =========================
# MARKET SIMULATION
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

    council = council_vote(market_state)

    result = run_market_feedback_loop(market_state)

    current_judgment = get_judgment()
    updated_judgment = apply_council_to_judgment(current_judgment, council)

    overwrite_judgment(updated_judgment)

    return {
        "status": "SIMULATION_COMPLETE",
        "market_state": market_state,
        "council": council,
        "result": result,
        "judgment": updated_judgment
    }


# =========================
# HEALTH
# =========================

@app.get("/")
def health():
    return {"status": "ClawBot alive"}

@app.get("/world")
def world():
    return get_judgment()


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
        "messages": [{"type": "text", "text": text}]
    }

    requests.post(LINE_REPLY_URL, headers=headers, json=payload, timeout=10)
