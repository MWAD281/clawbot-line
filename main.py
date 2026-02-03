from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time
import random

app = FastAPI(
    title="ClawBot Phase 56",
    description="Autonomous Simulation API",
    version="56.0"
)

# -------------------------
# In-memory state (safe)
# -------------------------
STATE = {
    "generation": 56,
    "cycle": 0,
    "agents": []
}

# -------------------------
# Root
# -------------------------
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 56 RUNNING",
        "generation": STATE["generation"],
        "cycle": STATE["cycle"],
        "agents": len(STATE["agents"])
    }

# -------------------------
# Dashboard
# -------------------------
@app.get("/dashboard")
def dashboard():
    return JSONResponse({
        "generation": STATE["generation"],
        "cycle": STATE["cycle"],
        "agents": STATE["agents"]
    })

# -------------------------
# Market Simulation
# -------------------------
@app.post("/simulate/market")
def simulate_market(payload: Dict[str, Any] = Body(...)):
    """
    Example payload:
    {
        "risk_level": "high",
        "volatility": "normal",
        "liquidity": "tight"
    }
    """

    STATE["cycle"] += 1

    agent = {
        "id": f"A-{len(STATE['agents'])+1}",
        "risk_level": payload.get("risk_level", "medium"),
        "volatility": payload.get("volatility", "normal"),
        "liquidity": payload.get("liquidity", "normal"),
        "decision": random.choice(["BUY", "SELL", "HOLD"]),
        "timestamp": int(time.time())
    }

    STATE["agents"].append(agent)

    return {
        "status": "ok",
        "cycle": STATE["cycle"],
        "agent": agent
    }
