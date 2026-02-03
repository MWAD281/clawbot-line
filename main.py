from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid

app = FastAPI(
    title="ClawBot Phase 37 – Darwinism Core",
    version="0.3.0"
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
# Models
# =========================
class MarketInput(BaseModel):
    risk_level: str
    trend: str
    volatility: str
    liquidity: str

# =========================
# Agent Registry
# =========================
AGENTS: Dict[str, dict] = {}

def spawn_agent(role: str):
    agent_id = str(uuid.uuid4())[:8]
    AGENTS[agent_id] = {
        "id": agent_id,
        "role": role,
        "score": 0.0,
        "alive": True,
        "created_at": datetime.utcnow().isoformat()
    }

# Initial agents
for role in ["Risk", "Macro", "Opportunist"]:
    spawn_agent(role)

# =========================
# Memory
# =========================
MEMORY: List[dict] = []

# =========================
# Agent Logic
# =========================
def agent_decision(agent, data: MarketInput):
    role = agent["role"]

    if role == "Risk":
        return "DEFENSIVE" if data.risk_level == "high" else "HOLD"

    if role == "Macro":
        if data.trend == "up":
            return "AGGRESSIVE"
        if data.trend == "down":
            return "DEFENSIVE"
        return "HOLD"

    if role == "Opportunist":
        return "AGGRESSIVE" if data.volatility in ["high", "extreme"] else "HOLD"

    return "HOLD"

# =========================
# Scoring System
# =========================
def evaluate(decision: str, data: MarketInput):
    # simple reward model (placeholder for real PnL)
    if decision == "AGGRESSIVE" and data.trend == "up":
        return +1.0
    if decision == "DEFENSIVE" and data.trend == "down":
        return +0.8
    if decision == "AGGRESSIVE" and data.trend == "down":
        return -1.2
    return -0.2

# =========================
# Darwinism Engine
# =========================
def darwin_cycle():
    dead = []
    for agent_id, agent in AGENTS.items():
        if agent["score"] < -3:
            agent["alive"] = False
            dead.append(agent_id)

    for agent_id in dead:
        del AGENTS[agent_id]
        spawn_agent(random.choice(["Risk", "Macro", "Opportunist"]))

# =========================
# Root
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 37 ONLINE",
        "agents_alive": len(AGENTS),
        "memory_records": len(MEMORY),
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# Simulation
# =========================
@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    results = []

    for agent in AGENTS.values():
        decision = agent_decision(agent, data)
        reward = evaluate(decision, data)
        agent["score"] += reward

        results.append({
            "agent_id": agent["id"],
            "role": agent["role"],
            "decision": decision,
            "reward": reward,
            "score": agent["score"]
        })

    darwin_cycle()

    record = {
        "input": data.dict(),
        "results": results,
        "agents_alive": len(AGENTS),
        "timestamp": datetime.utcnow().isoformat()
    }

    MEMORY.append(record)

    return {
        "engine": "ClawBot Phase 37",
        "cycle_result": results,
        "agents_alive": len(AGENTS)
    }

# =========================
# Dashboard
# =========================
@app.get("/dashboard")
def dashboard():
    return {
        "phase": 37,
        "agents": list(AGENTS.values()),
        "memory_size": len(MEMORY),
        "last_cycle": MEMORY[-1] if MEMORY else None,
        "status": "EVOLVING",
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# LINE Webhook Stub
# =========================
@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
