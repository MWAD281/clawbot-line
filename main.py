from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict
import random
import time

app = FastAPI(
    title="ClawBot Phase 70 – Clean Core",
    version="70.0.0",
    description="Stable clean base before Phase 71–75"
)

# =========================
# Data Models
# =========================

class MarketInput(BaseModel):
    volatility: Optional[str] = "normal"
    regime: Optional[str] = "neutral"
    liquidity: Optional[str] = "normal"


class SimulationResult(BaseModel):
    generation: int
    agent_id: int
    decision: str
    confidence: float
    timestamp: float


# =========================
# Root
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": 70,
        "ready_for_next_phases": True
    }


# =========================
# Market Simulation (Basic)
# =========================

@app.post("/simulate/market", response_model=SimulationResult)
def simulate_market(input: MarketInput):
    decision_pool = ["BUY", "SELL", "HOLD"]

    decision = random.choice(decision_pool)

    return SimulationResult(
        generation=70,
        agent_id=random.randint(1, 5),
        decision=decision,
        confidence=round(random.uniform(0.5, 0.95), 2),
        timestamp=time.time()
    )


# =========================
# Health Check
# =========================

@app.get("/health")
def health():
    return {"ok": True}
