from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional
import random
import uuid
import copy
import math

app = FastAPI(
    title="ClawBot Phase 43 – Paper Trading Engine",
    version="0.9.0"
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
    volatility: str            # normal | high | extreme
    liquidity: str             # loose | normal | tight
    momentum: float            # -1.0 .. +1.0
    price: float               # synthetic price feed

# =========================
# Global Config
# =========================
POPULATION_SIZE = 6
INITIAL_CAPITAL = 100_000.0
MAX_DRAWDOWN = 0.35
CRITICAL_DRAWDOWN = 0.20
TAKER_FEE = 0.0006
SLIPPAGE_BASE = 0.0005
HOF_LIMIT = 8

GENERATION = 1
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []
AUDIT_LOG: List[dict] = []

# =========================
# Genetics
# =========================
def random_gene():
    return {
        "aggression": round(random.uniform(0.1, 1.0), 2),
        "risk_tolerance": round(random.uniform(0.1, 1.0), 2),
        "adaptability": round(random.uniform(0.1, 1.0), 2),
        "base_position": round(random.uniform(0.05, 0.5), 2),
        "trend_bias": random.choice(["bull", "bear", "neutral"])
    }

def mutate_gene(g):
    g2 = copy.deepcopy(g)
    k = random.choice(list(g2.keys()))
    if isinstance(g2[k], float):
        g2[k] = round(min(1.0, max(0.05, g2[k] + random.uniform(-0.15, 0.15))), 2)
    else:
        g2[k] = random.choice(["bull", "bear", "neutral"])
    return g2

def crossover(g1, g2):
    return {k: random.choice([g1[k], g2[k]]) for k in g1}

# =========================
# Agent Factory
# =========================
def spawn_agent(parent_gene=None):
    aid = str(uuid.uuid4())[:8]
    gene = mutate_gene(parent_gene) if parent_gene else random_gene()
    AGENTS[aid] = {
        "id": aid,
        "gene": gene,
        "capital": INITIAL_CAPITAL,
        "equity": INITIAL_CAPITAL,
        "peak": INITIAL_CAPITAL,
        "alive": True,
        "position": None,   # {side, entry, size}
        "born_gen": GENERATION
    }

for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Market Regime
# =========================
def detect_regime(m: MarketInput):
    if m.momentum > 0.4:
        return "BULL"
    if m.momentum < -0.4:
        return "BEAR"
    return "SIDEWAYS"

# =========================
# Decision Engine
# =========================
def decide(agent, regime):
    bias = agent["gene"]["trend_bias"].upper()
    adapt = agent["gene"]["adaptability"]

    if bias == regime:
        return "ENTER"
    if adapt > 0.7:
        return "SCALP"
    return "HOLD"

# =========================
# Execution Engine
# =========================
def slippage(market: MarketInput):
    mult = {"loose": 0.8, "normal": 1.0, "tight": 1.6}[market.liquidity]
    return SLIPPAGE_BASE * mult

def position_size(agent, regime):
    base = agent["gene"]["base_position"]
    risk = agent["gene"]["risk_tolerance"]
    adj = 1.0 if regime != "SIDEWAYS" else 0.6
    return max(0.01, min(0.7, base * risk * adj))

def open_position(agent, side, price, size, market):
    slip = slippage(market)
    fill = price * (1 + slip if side == "LONG" else 1 - slip)
    fee = agent["capital"] * size * TAKER_FEE
    agent["capital"] -= fee
    agent["position"] = {
        "side": side,
        "entry": fill,
        "size": size
    }
    return fill, fee

def close_position(agent, price, market):
    pos = agent["position"]
    slip = slippage(market)
    exit_price = price * (1 - slip if pos["side"] == "LONG" else 1 + slip)
    pnl = (exit_price - pos["entry"]) / pos["entry"]
    if pos["side"] == "SHORT":
        pnl = -pnl
    gross = agent["capital"] * pos["size"] * pnl
    fee = abs(gross) * TAKER_FEE
    agent["capital"] += gross - fee
    agent["position"] = None
    return gross - fee

# =========================
# Risk Manager
# =========================
def risk_manager(agent):
    agent["equity"] = agent["capital"]
    agent["peak"] = max(agent["peak"], agent["equity"])
    dd = 1 - agent["equity"] / agent["peak"]

    if dd >= MAX_DRAWDOWN:
        agent["alive"] = False
        return "KILL", round(dd, 3)

    if dd >= CRITICAL_DRAWDOWN and agent["position"]:
        agent["position"]["size"] *= 0.5
        return "REDUCE", round(dd, 3)

    return "OK", round(dd, 3)

# =========================
# Evolution
# =========================
def evolve():
    global GENERATION, AGENTS
    GENERATION += 1

    alive = [a for a in AGENTS.values() if a["alive"]]
    if not alive:
        AGENTS.clear()
        for _ in range(POPULATION_SIZE):
            spawn_agent()
        return

    ranked = sorted(alive, key=lambda a: a["capital"], reverse=True)
    champ = ranked[0]

    HALL_OF_FAME.append({
        "gene": champ["gene"],
        "capital": round(champ["capital"], 2),
        "gen": GENERATION
    })
    HALL_OF_FAME.sort(key=lambda x: x["capital"], reverse=True)
    del HALL_OF_FAME[HOF_LIMIT:]

    survivors = ranked[:max(2, len(ranked)//2)]
    AGENTS = {a["id"]: a for a in survivors}

    while len(AGENTS) < POPULATION_SIZE:
        g = crossover(champ["gene"], random.choice(survivors)["gene"])
        spawn_agent(g)

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 43 ONLINE",
        "generation": GENERATION,
        "agents": len(AGENTS),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/simulate/market")
def simulate(market: MarketInput):
    regime = detect_regime(market)
    cycle = []

    for agent in AGENTS.values():
        if not agent["alive"]:
            continue

        decision = decide(agent, regime)

        # Exit logic
        if agent["position"] and decision in ["HOLD", "SCALP"]:
            pnl = close_position(agent, market.price, market)
        else:
            pnl = 0.0

        # Entry logic
        if not agent["position"] and decision in ["ENTER", "SCALP"]:
            side = "LONG" if regime == "BULL" else "SHORT"
            size = position_size(agent, regime)
            fill, fee = open_position(agent, side, market.price, size, market)

        risk_action, dd = risk_manager(agent)

        cycle.append({
            "agent": agent["id"],
            "decision": decision,
            "regime": regime,
            "capital": round(agent["capital"], 2),
            "drawdown": dd,
            "risk": risk_action,
            "alive": agent["alive"]
        })

        AUDIT_LOG.append({
            "time": datetime.utcnow().isoformat(),
            "agent": agent["id"],
            "decision": decision,
            "capital": agent["capital"]
        })

    evolve()

    return {
        "phase": 43,
        "generation": GENERATION,
        "regime": regime,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]]),
        "cycle": cycle
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 43,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "audit_logs": len(AUDIT_LOG),
        "status": "PAPER_TRADING_ACTIVE"
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
