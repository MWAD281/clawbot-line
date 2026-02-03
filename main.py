from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time
import uuid
import random

app = FastAPI(title="ClawBot Phase 55 – Agent Death & Rebirth Engine")

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
DEATH_LOG: List[Dict] = []

CONFIDENCE_DECAY_RATE = 0.02
CONFIDENCE_REWARD_RATE = 0.05
SCORE_GOOD_THRESHOLD = 0.5

CAPITAL_GROWTH_RATE = 0.10
CAPITAL_SHRINK_RATE = 0.08

MIN_CAPITAL = 0.1
DEATH_CAPITAL_THRESHOLD = 0.2
DEATH_CONFIDENCE_THRESHOLD = 0.2

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
    return round((ret * 0.6) - (dd * 0.3) - (risk * 0.1), 4)

def apply_confidence_decay():
    now = time.time()
    for agent in AGENTS.values():
        last = agent.get("last_evaluated", agent["created_at"])
        if now - last > 60:
            agent["confidence"] = max(0.0, round(agent["confidence"] - CONFIDENCE_DECAY_RATE, 4))

def adjust_capital(agent: Dict):
    c = agent["confidence"]

    if c >= 0.7:
        agent["capital"] *= (1 + CAPITAL_GROWTH_RATE * c)
    elif c <= 0.3:
        agent["capital"] *= (1 - CAPITAL_SHRINK_RATE * (1 - c))

    agent["capital"] = round(max(agent["capital"], MIN_CAPITAL), 4)

def is_dead(agent: Dict) -> bool:
    return agent["capital"] < DEATH_CAPITAL_THRESHOLD and agent["confidence"] < DEATH_CONFIDENCE_THRESHOLD

def mutate_strategy(base: str) -> str:
    mutations = ["aggressive", "defensive", "scalping", "trend", "mean-reversion"]
    return f"{base}-{random.choice(mutations)}"

def spawn_agent(parent_strategy: str = "seed"):
    agent_id = str(uuid.uuid4())
    AGENTS[agent_id] = {
        "name": f"Agent-{agent_id[:5]}",
        "strategy": mutate_strategy(parent_strategy),
        "capital": 1.0,
        "performance_score": None,
        "confidence": 0.5,
        "created_at": time.time(),
        "last_evaluated": None
    }

# =========================================================
# Routes
# =========================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 55 ONLINE"}

@app.get("/dashboard")
def dashboard():
    apply_confidence_decay()
    return {
        "market": MARKET_STATE,
        "agents": AGENTS,
        "alive_agents": len(AGENTS),
        "death_count": len(DEATH_LOG),
        "timestamp": time.time()
    }

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    MARKET_STATE.update({
        "risk_level": data.risk_level,
        "volatility": data.volatility,
        "liquidity": data.liquidity,
        "last_update": time.time()
    })
    return {"status": "market_updated"}

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

@app.post("/agent/evaluate")
def evaluate_agent(data: AgentPerformance):
    if data.agent_id not in AGENTS:
        return {"error": "agent_not_found"}

    agent = AGENTS[data.agent_id]
    score = calculate_score(data.return_pct, data.drawdown_pct, data.risk_behavior)

    agent["performance_score"] = score
    agent["last_evaluated"] = time.time()

    if score >= SCORE_GOOD_THRESHOLD:
        agent["confidence"] = min(1.0, agent["confidence"] + CONFIDENCE_REWARD_RATE)
    else:
        agent["confidence"] = max(0.0, agent["confidence"] - CONFIDENCE_DECAY_RATE)

    adjust_capital(agent)

    EVALUATION_LOG.append({
        "agent_id": data.agent_id,
        "score": score,
        "confidence": agent["confidence"],
        "capital": agent["capital"],
        "timestamp": time.time()
    })

    # ☠️ Death Check
    if is_dead(agent):
        DEATH_LOG.append({
            "agent_id": data.agent_id,
            "strategy": agent["strategy"],
            "capital": agent["capital"],
            "confidence": agent["confidence"],
            "timestamp": time.time()
        })

        parent_strategy = random.choice(list(AGENTS.values()))["strategy"] if len(AGENTS) > 1 else "seed"
        del AGENTS[data.agent_id]
        spawn_agent(parent_strategy)

        return {"status": "agent_died_and_reborn"}

    return {
        "status": "agent_evaluated",
        "score": score,
        "confidence": agent["confidence"],
        "capital": agent["capital"]
    }

@app.get("/agents/deaths")
def death_history():
    return {
        "count": len(DEATH_LOG),
        "records": DEATH_LOG[-50:]
    }
