from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time
import uuid

app = FastAPI(title="ClawBot Phase 54 – Capital Weighting Engine")

# =========================================================
# Global States
# =========================================================

MARKET_STATE = {
    "risk_level": "normal",
    "volatility": "normal",
    "liquidity": "normal",
    "last_update": None
}

AGENTS: Dict[str, Dict] = {}
EVALUATION_LOG: List[Dict] = []

CONFIDENCE_DECAY_RATE = 0.02
CONFIDENCE_REWARD_RATE = 0.05
SCORE_GOOD_THRESHOLD = 0.5

CAPITAL_GROWTH_RATE = 0.10     # max growth per evaluation
CAPITAL_SHRINK_RATE = 0.08     # shrink when low confidence
MIN_CAPITAL = 0.1

# =========================================================
# Schemas
# =========================================================

class MarketInput(BaseModel):
    risk_level: str
    volatility: str
    liquidity: str

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

def calculate_score(ret: float, dd: float, risk: float) -> float:
    score = (ret * 0.6) - (dd * 0.3) - (risk * 0.1)
    return round(score, 4)

def apply_confidence_decay():
    now = time.time()
    for agent in AGENTS.values():
        last = agent.get("last_evaluated", agent["created_at"])
        if now - last > 60:
            agent["confidence"] = max(
                0.0,
                round(agent["confidence"] - CONFIDENCE_DECAY_RATE, 4)
            )

def adjust_capital(agent: Dict):
    confidence = agent["confidence"]

    if confidence >= 0.7:
        growth = 1 + (CAPITAL_GROWTH_RATE * confidence)
        agent["capital"] = round(agent["capital"] * growth, 4)

    elif confidence <= 0.3:
        shrink = 1 - (CAPITAL_SHRINK_RATE * (1 - confidence))
        agent["capital"] = round(agent["capital"] * shrink, 4)

    agent["capital"] = max(agent["capital"], MIN_CAPITAL)

# =========================================================
# Routes
# =========================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 54 ONLINE"}

# -------------------------
# Dashboard
# -------------------------
@app.get("/dashboard")
def dashboard():
    apply_confidence_decay()
    return {
        "market_state": MARKET_STATE,
        "agents": AGENTS,
        "evaluation_log_count": len(EVALUATION_LOG),
        "timestamp": time.time()
    }

# -------------------------
# Market Simulation
# -------------------------
@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    MARKET_STATE.update({
        "risk_level": data.risk_level,
        "volatility": data.volatility,
        "liquidity": data.liquidity,
        "last_update": time.time()
    })
    return {"status": "market_state_updated", "market_state": MARKET_STATE}

# -------------------------
# Agent Creation
# -------------------------
@app.post("/agent/create")
def create_agent(data: AgentCreate):
    agent_id = str(uuid.uuid4())

    AGENTS[agent_id] = {
        "name": data.name,
        "strategy": data.strategy,
        "capital": 1.0,
        "performance_score": None,
        "confidence": 0.5,
        "created_at": time.time(),
        "last_evaluated": None
    }

    return {"status": "agent_created", "agent_id": agent_id}

# -------------------------
# Agent Evaluation
# -------------------------
@app.post("/agent/evaluate")
def evaluate_agent(data: AgentPerformance):
    if data.agent_id not in AGENTS:
        return {"error": "agent_not_found"}

    score = calculate_score(
        data.return_pct,
        data.drawdown_pct,
        data.risk_behavior
    )

    agent = AGENTS[data.agent_id]
    agent["performance_score"] = score
    agent["last_evaluated"] = time.time()

    # Confidence logic
    if score >= SCORE_GOOD_THRESHOLD:
        agent["confidence"] = min(
            1.0,
            round(agent["confidence"] + CONFIDENCE_REWARD_RATE, 4)
        )
    else:
        agent["confidence"] = max(
            0.0,
            round(agent["confidence"] - CONFIDENCE_DECAY_RATE, 4)
        )

    # Capital adjustment
    adjust_capital(agent)

    log = {
        "agent_id": data.agent_id,
        "return": data.return_pct,
        "drawdown": data.drawdown_pct,
        "risk": data.risk_behavior,
        "score": score,
        "confidence": agent["confidence"],
        "capital": agent["capital"],
        "timestamp": time.time()
    }

    EVALUATION_LOG.append(log)

    return {
        "status": "agent_evaluated",
        "score": score,
        "confidence": agent["confidence"],
        "capital": agent["capital"]
    }

# -------------------------
# Evaluation History
# -------------------------
@app.get("/agent/evaluations")
def evaluation_history():
    return {
        "count": len(EVALUATION_LOG),
        "records": EVALUATION_LOG[-50:]
    }
