from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List

app = FastAPI(
    title="ClawBot Phase 36 – Multi-Agent Core",
    version="0.2.0"
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Memory (in-memory)
# =========================
MEMORY: List[dict] = []

# =========================
# Root
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 36 ONLINE",
        "agents": 3,
        "memory_size": len(MEMORY),
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# Models
# =========================
class MarketInput(BaseModel):
    risk_level: str
    trend: str
    volatility: str
    liquidity: str

# =========================
# Agents
# =========================
def risk_agent(data: MarketInput):
    if data.risk_level == "high":
        return ("DEFENSIVE", 0.8)
    return ("HOLD", 0.5)

def macro_agent(data: MarketInput):
    if data.trend == "up":
        return ("AGGRESSIVE", 0.7)
    if data.trend == "down":
        return ("DEFENSIVE", 0.6)
    return ("HOLD", 0.5)

def opportunist_agent(data: MarketInput):
    if data.volatility == "extreme":
        return ("AGGRESSIVE", 0.6)
    return ("HOLD", 0.4)

# =========================
# Voting Engine
# =========================
def vote(decisions):
    score = {}
    for decision, confidence in decisions:
        score[decision] = score.get(decision, 0) + confidence
    final = max(score, key=score.get)
    return final, score

# =========================
# Simulation Endpoint
# =========================
@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    decisions = [
        risk_agent(data),
        macro_agent(data),
        opportunist_agent(data),
    ]

    final_decision, score_table = vote(decisions)

    record = {
        "input": data.dict(),
        "agents": decisions,
        "final_decision": final_decision,
        "scores": score_table,
        "timestamp": datetime.utcnow().isoformat()
    }

    MEMORY.append(record)

    return {
        "decision": final_decision,
        "scores": score_table,
        "agents": [
            {"name": "RiskAgent", "vote": decisions[0][0]},
            {"name": "MacroAgent", "vote": decisions[1][0]},
            {"name": "OpportunistAgent", "vote": decisions[2][0]},
        ],
        "engine": "ClawBot Phase 36"
    }

# =========================
# Dashboard
# =========================
@app.get("/dashboard")
def dashboard():
    return {
        "system": "ClawBot",
        "phase": 36,
        "agents": ["RiskAgent", "MacroAgent", "OpportunistAgent"],
        "memory_records": len(MEMORY),
        "last_decision": MEMORY[-1] if MEMORY else None,
        "status": "ONLINE",
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# LINE Webhook (stub)
# =========================
@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.json()
    return {"ok": True}
