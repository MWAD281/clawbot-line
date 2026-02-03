from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time
import uuid
import random

app = FastAPI(title="ClawBot Phase 56 – Agent Alliance & Voting Engine")

# =========================================================
# Global States
# =========================================================

MARKET_STATE = {
    "direction": "neutral",
    "last_vote": None
}

AGENTS: Dict[str, Dict] = {}
EVALUATION_LOG: List[Dict] = []
DEATH_LOG: List[Dict] = []
VOTE_LOG: List[Dict] = []

CONFIDENCE_DECAY_RATE = 0.02
CONFIDENCE_REWARD_RATE = 0.05

CAPITAL_GROWTH_RATE = 0.12
CAPITAL_SHRINK_RATE = 0.10

DEATH_CAPITAL_THRESHOLD = 0.2
DEATH_CONFIDENCE_THRESHOLD = 0.2

# =========================================================
# Schemas
# =========================================================

class AgentCreate(BaseModel):
    name: str
    strategy: str

class AgentPerformance(BaseModel):
    agent_id: str
    return_pct: float
    drawdown_pct: float
    risk_behavior: float

# =========================================================
# Utility
# =========================================================

def calculate_score(ret, dd, risk):
    return round((ret * 0.6) - (dd * 0.3) - (risk * 0.1), 4)

def alliance(strategy: str) -> str:
    if "bull" in strategy or "trend" in strategy or "aggressive" in strategy:
        return "bull"
    if "bear" in strategy or "defensive" in strategy:
        return "bear"
    return "neutral"

def adjust_capital(agent, boost: bool):
    if boost:
        agent["capital"] *= (1 + CAPITAL_GROWTH_RATE * agent["confidence"])
        agent["confidence"] = min(1.0, agent["confidence"] + CONFIDENCE_REWARD_RATE)
    else:
        agent["capital"] *= (1 - CAPITAL_SHRINK_RATE * (1 - agent["confidence"]))
        agent["confidence"] = max(0.0, agent["confidence"] - CONFIDENCE_DECAY_RATE)

    agent["capital"] = round(agent["capital"], 4)
    agent["confidence"] = round(agent["confidence"], 4)

def is_dead(agent):
    return agent["capital"] < DEATH_CAPITAL_THRESHOLD and agent["confidence"] < DEATH_CONFIDENCE_THRESHOLD

def spawn_agent(parent_strategy="seed"):
    aid = str(uuid.uuid4())
    AGENTS[aid] = {
        "name": f"Agent-{aid[:5]}",
        "strategy": parent_strategy + "-" + random.choice(["trend", "mean", "scalp"]),
        "capital": 1.0,
        "confidence": 0.5,
        "created_at": time.time(),
        "last_evaluated": None
    }

# =========================================================
# Routes
# =========================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 56 ONLINE"}

@app.get("/dashboard")
def dashboard():
    alliances = {"bull": 0, "bear": 0, "neutral": 0}
    for a in AGENTS.values():
        alliances[alliance(a["strategy"])] += 1

    return {
        "market": MARKET_STATE,
        "agents": AGENTS,
        "alliances": alliances,
        "deaths": len(DEATH_LOG),
        "votes": len(VOTE_LOG),
        "timestamp": time.time()
    }

@app.post("/agent/create")
def create_agent(data: AgentCreate):
    aid = str(uuid.uuid4())
    AGENTS[aid] = {
        "name": data.name,
        "strategy": data.strategy,
        "capital": 1.0,
        "confidence": 0.5,
        "created_at": time.time(),
        "last_evaluated": None
    }
    return {"agent_id": aid}

@app.post("/agent/evaluate")
def evaluate_agent(data: AgentPerformance):
    if data.agent_id not in AGENTS:
        return {"error": "agent_not_found"}

    agent = AGENTS[data.agent_id]
    score = calculate_score(data.return_pct, data.drawdown_pct, data.risk_behavior)
    agent["last_evaluated"] = time.time()

    if score > 0:
        agent["confidence"] += CONFIDENCE_REWARD_RATE
    else:
        agent["confidence"] -= CONFIDENCE_DECAY_RATE

    agent["confidence"] = max(0.0, min(1.0, agent["confidence"]))

    # =====================================================
    # Voting Phase
    # =====================================================

    vote_power = {"bull": 0, "bear": 0, "neutral": 0}

    for a in AGENTS.values():
        camp = alliance(a["strategy"])
        vote_power[camp] += a["confidence"] * a["capital"]

    winner = max(vote_power, key=vote_power.get)
    MARKET_STATE["direction"] = winner
    MARKET_STATE["last_vote"] = time.time()

    VOTE_LOG.append({
        "winner": winner,
        "vote_power": vote_power,
        "timestamp": time.time()
    })

    # =====================================================
    # Reward / Punish
    # =====================================================

    for aid, a in list(AGENTS.items()):
        boost = alliance(a["strategy"]) == winner
        adjust_capital(a, boost)

        if is_dead(a):
            DEATH_LOG.append({
                "agent_id": aid,
                "strategy": a["strategy"],
                "timestamp": time.time()
            })
            parent = random.choice(list(AGENTS.values()))["strategy"] if len(AGENTS) > 1 else "seed"
            del AGENTS[aid]
            spawn_agent(parent)

    return {
        "status": "vote_complete",
        "winner": winner,
        "vote_power": vote_power
    }

@app.get("/votes")
def vote_history():
    return VOTE_LOG[-20:]

@app.get("/agents/deaths")
def death_history():
    return DEATH_LOG[-20:]
