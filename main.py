from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="ClawBot Phase 35 – LINE Bridge",
    version="0.1.0"
)

# =========================
# CORS (สำคัญมาก)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # production จริงค่อย lock domain
    allow_credentials=True,
    allow_methods=["*"],          # GET POST OPTIONS
    allow_headers=["*"],
)

# =========================
# Root
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 35 ONLINE",
        "epoch": 0,
        "generation": 1,
        "pressure": 1.0,
        "deception": 0.0,
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# LINE Webhook
# =========================
@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.json()
    return {"ok": True}

# =========================
# Market Simulation
# =========================
class MarketInput(BaseModel):
    risk_level: str
    trend: str
    volatility: str
    liquidity: str

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    decision = "HOLD"

    if data.risk_level == "high" and data.trend == "down":
        decision = "DEFENSIVE"
    elif data.risk_level == "low" and data.trend == "up":
        decision = "AGGRESSIVE"

    return {
        "input": data.dict(),
        "decision": decision,
        "confidence": 0.72,
        "engine": "ClawBot Phase 35",
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# Dashboard
# =========================
@app.get("/dashboard")
def dashboard():
    return {
        "system": "ClawBot",
        "phase": 35,
        "status": "ONLINE",
        "agents": 1,
        "uptime": "stable",
        "last_check": datetime.utcnow().isoformat()
    }
