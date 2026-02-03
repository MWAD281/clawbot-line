from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List
import random
import time
import uuid

app = FastAPI(
    title="ClawBot Phase 95 – Live Ready (Safe Mode)",
    version="95.0.0",
    description="Live exchange ready with multi-layer safety lock"
)

# =========================
# CONFIG
# =========================

PHASE = 95
MAX_AGENTS = 5

TRADE_MODE = "sandbox"  
# sandbox | testnet | live (live ต้อง unlock)

LIVE_UNLOCK = False     # <<< ต้องเปิดเองถึงจะยิงเงินจริง

INITIAL_CAPITAL = 100_000.0
MAX_RISK_PER_TRADE = 0.015      # ลดจากเดิม
STOP_LOSS_PCT = 0.03
TAKE_PROFIT_PCT = 0.06

MAX_AGENT_DRAWDOWN = -0.15
GLOBAL_MAX_DRAWDOWN = -0.25
MIN_FITNESS = 0.55
MUTATION_RATE = 0.08

AGENTS: Dict[int, Dict] = {}
TRADE_LOG: List[Dict] = []

# =========================
# MODELS
# =========================

class MarketInput(BaseModel):
    price: float
    symbol: str = "BTCUSDT"


class TradeResult(BaseModel):
    trade_id: str
    agent_id: int
    decision: str
    size: float
    entry_price: float
    exit_price: float
    pnl: float
    capital_after: float
    fitness: float
    mode: str
    note: str
    timestamp: float

# =========================
# AGENT CORE
# =========================

def create_genome():
    return {
        "risk": round(random.uniform(0.25, 0.7), 2),
        "aggression": round(random.uniform(0.25, 0.7), 2),
        "patience": round(random.uniform(0.25, 0.7), 2),
    }


def spawn_agent(i):
    AGENTS[i] = {
        "genome": create_genome(),
        "fitness": round(random.uniform(0.6, 0.8), 3),
        "capital": INITIAL_CAPITAL / MAX_AGENTS,
        "peak_capital": INITIAL_CAPITAL / MAX_AGENTS,
        "alive": True,
        "wins": 0,
        "losses": 0,
        "trades": 0
    }


for i in range(1, MAX_AGENTS + 1):
    spawn_agent(i)

# =========================
# DECISION SYSTEM
# =========================

def agent_decide(genome):
    r = random.random()
    if r < genome["aggression"]:
        return "BUY"
    if r > 1 - genome["risk"]:
        return "SELL"
    return "HOLD"


def position_size(agent_capital, confidence):
    base = agent_capital * MAX_RISK_PER_TRADE
    drawdown_penalty = max(0.3, agent_capital / (INITIAL_CAPITAL / MAX_AGENTS))
    size = base * confidence * drawdown_penalty
    return round(size, 2)

# =========================
# EXCHANGE EXECUTION
# =========================

def execute_trade(decision, price, size):
    if decision == "HOLD":
        return price, price, 0.0

    entry = price * (1 + random.uniform(-0.0008, 0.0008))
    move = random.uniform(-0.06, 0.07)

    raw_exit = entry * (1 + move)
    sl = entry * (1 - STOP_LOSS_PCT)
    tp = entry * (1 + TAKE_PROFIT_PCT)

    exit_price = min(max(raw_exit, sl), tp)
    pnl = (exit_price - entry) / entry * size

    return round(entry, 4), round(exit_price, 4), round(pnl, 2)

# =========================
# ROOT / STATUS
# =========================

@app.get("/")
def root():
    return {
        "phase": PHASE,
        "mode": TRADE_MODE,
        "live_unlocked": LIVE_UNLOCK,
        "agents_alive": sum(a["alive"] for a in AGENTS.values()),
        "trades": len(TRADE_LOG)
    }


@app.get("/health")
def health():
    return {"ok": True, "phase": PHASE, "mode": TRADE_MODE}

# =========================
# CORE SIMULATION
# =========================

@app.post("/simulate/market", response_model=TradeResult)
def simulate_market(input: MarketInput):

    if TRADE_MODE == "live" and not LIVE_UNLOCK:
        return TradeResult(
            trade_id="LOCKED",
            agent_id=-1,
            decision="BLOCKED",
            size=0,
            entry_price=0,
            exit_price=0,
            pnl=0,
            capital_after=sum(a["capital"] for a in AGENTS.values()),
            fitness=0,
            mode=TRADE_MODE,
            note="LIVE MODE LOCKED",
            timestamp=time.time()
        )

    alive = [i for i, a in AGENTS.items() if a["alive"]]
    agent_id = random.choice(alive)
    agent = AGENTS[agent_id]

    genome = agent["genome"]
    decision = agent_decide(genome)
    confidence = random.uniform(0.5, 0.9)

    size = position_size(agent["capital"], confidence)
    entry, exit_p, pnl = execute_trade(decision, input.price, size)

    agent["capital"] += pnl
    agent["peak_capital"] = max(agent["peak_capital"], agent["capital"])
    agent["trades"] += 1

    if pnl > 0:
        agent["wins"] += 1
    else:
        agent["losses"] += 1

    agent["fitness"] = max(0.0, min(1.0, agent["fitness"] + pnl / max(agent["capital"], 1)))

    note = "ok"

    if (agent["capital"] - agent["peak_capital"]) / agent["peak_capital"] <= MAX_AGENT_DRAWDOWN:
        agent["alive"] = False
        spawn_agent(agent_id)
        note = "agent killed → reborn"

    trade = {
        "id": str(uuid.uuid4()),
        "agent": agent_id,
        "decision": decision,
        "entry": entry,
        "exit": exit_p,
        "pnl": pnl,
        "mode": TRADE_MODE,
        "time": time.time()
    }
    TRADE_LOG.append(trade)

    return TradeResult(
        trade_id=trade["id"],
        agent_id=agent_id,
        decision=decision,
        size=size,
        entry_price=entry,
        exit_price=exit_p,
        pnl=pnl,
        capital_after=round(agent["capital"], 2),
        fitness=round(agent["fitness"], 3),
        mode=TRADE_MODE,
        note=note,
        timestamp=trade["time"]
    )

# =========================
# MONITORING
# =========================

@app.get("/agents")
def agents():
    return AGENTS


@app.get("/trades")
def trades():
    return TRADE_LOG[-50:]


@app.post("/unlock_live")
def unlock_live():
    global LIVE_UNLOCK
    LIVE_UNLOCK = True
    return {"live": "UNLOCKED"}
