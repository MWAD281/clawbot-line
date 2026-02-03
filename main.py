from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import time

app = FastAPI(title="ClawBot Phase 51 – External Market Injection")

# ======================
# In-memory market state
# ======================
MARKET_STATE = {
    "risk_level": "normal",
    "volatility": "normal",
    "liquidity": "normal",
    "last_update": None
}

# ======================
# Schemas
# ======================
class MarketInput(BaseModel):
    risk_level: str
    volatility: str
    liquidity: str

# ======================
# Root
# ======================
@app.get("/")
def root():
    return {"status": "ClawBot Phase 51 ONLINE"}

# ======================
# Dashboard
# ======================
@app.get("/dashboard")
def dashboard():
    return {
        "market_state": MARKET_STATE,
        "timestamp": time.time()
    }

# ======================
# Phase 51: External Market Injection
# ======================
@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    MARKET_STATE.update({
        "risk_level": data.risk_level,
        "volatility": data.volatility,
        "liquidity": data.liquidity,
        "last_update": time.time()
    })

    return {
        "status": "market_state_updated",
        "market_state": MARKET_STATE
    }
