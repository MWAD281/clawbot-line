from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time
import uuid

app = FastAPI(title="ClawBot Phase 52 – Agent Self Evaluation")

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
    risk_behavior: float  # 0.0 = conservative, 1.0 = aggressive

# =========================================================
# Utility
# =========================================================

def calculate_score(ret: float, dd: float, risk: float) -> float:
    """
    Core self-evaluation formula
    """
    score = (ret * 0.6) - (dd * 0.3) - (risk * 0.1)
    return round(score, 4)

# =========================================================
# Routes
# =========================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 52 ONLINE"}

# -------------------------
# Dashboard
# -------------------------
@app.get("/dashboard")
def dashboard():
    return {
        "market_state": MARKET_STATE,
        "agents": AGENTS,
        "evaluation_log_count": len(EVALUATION_LOG),
        "timestamp": time.time()
    }

# -------------------------
# Phase 51: Market Injection
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
# Phase 52: Agent Creation
# -------------------------
@app.post("/agent/create")
def create_agent(data: AgentCreate):
    agent_id = str(uuid.uuid4())

    AGENTS[agent_id] = {
        "name": data.name,
        "strategy": data.strategy,
        "capital": 1.0,
        "performance_score": None,
        "created_at": time.time()
    }

    return {"status": "agent_created", "agent_id": agent_id}

# -------------------------
# Phase 52: Self Evaluation
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

    AGENTS[data.agent_id]["performance_score"] = score

    log = {
        "agent_id": data.agent_id,
        "return": data.return_pct,
        "drawdown": data.drawdown_pct,
        "risk": data.risk_behavior,
        "score": score,
        "timestamp": time.time()
    }

    EVALUATION_LOG.append(log)

    return {
        "status": "agent_evaluated",
        "score": score
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
