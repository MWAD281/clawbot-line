from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import random
import uuid
import copy
import statistics
import math
import time

app = FastAPI(
    title="ClawBot Phase 49 – Memory Compression + Forgetting Curve",
    version="1.0.0"
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
    volatility: str
    liquidity: str
    momentum: float
    price: float

# =========================
# Config
# =========================
POPULATION_SIZE = 8
TOTAL_CAPITAL = 800_000.0
BASE_CAPITAL = TOTAL_CAPITAL / POPULATION_SIZE

MAX_DRAWDOWN = 0.35
PORTFOLIO_MAX_DD = 0.25

VAR_LIMIT = 0.04
RISK_REDUCTION_FACTOR = 0.5

TAKER_FEE = 0.0006
SLIPPAGE_BASE = 0.0005

RAW_MEMORY_LIMIT = 60
COMPRESSED_MEMORY_LIMIT = 20
HOF_LIMIT = 10

FORGET_HALF_LIFE = 20  # ยิ่งมาก ยิ่งลืมช้า (เป็นจำนวน cycle)

GENERATION = 1
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []

STRATEGY_ROLES = ["TREND", "MEAN", "SCALP", "CRISIS"]

# =========================
# Genetics
# =========================
def random_gene():
    return {
        "aggression": round(random.uniform(0.2, 1.0), 2),
        "risk_tolerance": round(random.uniform(0.2, 1.0), 2),
        "adaptability": round(random.uniform(0.2, 1.0), 2),
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
def spawn_agent(parent_gene=None, role=None, capital=BASE_CAPITAL):
    aid = str(uuid.uuid4())[:8]
    gene = mutate_gene(parent_gene) if parent_gene else random_gene()
    AGENTS[aid] = {
        "id": aid,
        "role": role or random.choice(STRATEGY_ROLES),
        "gene": gene,
        "capital": capital,
        "equity": capital,
        "peak": capital,
        "alive": True,
        "position": None,
        "raw_memory": [],
        "compressed_memory": [],
        "returns": [],
        "born_gen": GENERATION
    }

for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Market Regime
# =========================
def detect_regime(m: MarketInput):
    if m.momentum > 0.6:
        return "BULL"
    if m.momentum < -0.6:
        return "BEAR"
    return "SIDEWAYS"

# =========================
# Memory Engine (NEW)
# =========================
def forgetting_weight(age):
    # Exponential decay
    return math.exp(-math.log(2) * age / FORGET_HALF_LIFE)

def compress_memory(agent):
    """
    รวม memory ที่ regime + momentum ใกล้กัน
    เก็บเฉพาะ 'แก่น' ที่มี impact สูง
    """
    buckets = {}
    for m in agent["raw_memory"]:
        key = (m["regime"], round(m["momentum"], 1))
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(m)

    compressed = []
    for (regime, mom), records in buckets.items():
        avg_pnl = statistics.mean(r["pnl"] for r in records)
        compressed.append({
            "regime": regime,
            "momentum": mom,
            "pnl": avg_pnl,
            "count": len(records),
            "timestamp": max(r["timestamp"] for r in records)
        })

    compressed.sort(key=lambda x: abs(x["pnl"]), reverse=True)
    agent["compressed_memory"] = compressed[:COMPRESSED_MEMORY_LIMIT]

def memory_bias(agent, snapshot):
    score = 0.0
    now = time.time()
    for m in agent["compressed_memory"]:
        if m["regime"] != snapshot["regime"]:
            continue
        age = snapshot["t"] - m["timestamp"]
        w = forgetting_weight(age)
        score += w * m["pnl"]
    return score

# =========================
# Decision Engine
# =========================
def decide(agent, market, regime):
    bias = memory_bias(agent, {
        "regime": regime,
        "t": time.time()
    })

    if agent["role"] == "TREND" and abs(market.momentum) > 0.4:
        return "ENTER"
    if agent["role"] == "MEAN" and regime == "SIDEWAYS":
        return "ENTER"
    if agent["role"] == "SCALP" and market.volatility == "high":
        return "SCALP"
    if agent["role"] == "CRISIS" and market.momentum < -0.7:
        return "ENTER"

    if bias > 0.015:
        return "ENTER"

    return "HOLD"

# =========================
# Execution
# =========================
def slippage(market):
    return SLIPPAGE_BASE * {"loose": 0.8, "normal": 1.0, "tight": 1.6}[market.liquidity]

def position_size(agent, risk_factor=1.0):
    return max(
        0.01,
        min(
            0.6,
            agent["gene"]["base_position"]
            * agent["gene"]["risk_tolerance"]
            * risk_factor
        )
    )

def open_position(agent, side, price, size, market):
    fill = price * (1 + slippage(market) if side == "LONG" else 1 - slippage(market))
    fee = agent["capital"] * size * TAKER_FEE
    agent["capital"] -= fee
    agent["position"] = {"side": side, "entry": fill, "size": size}

def close_position(agent, price, market, regime, momentum):
    pos = agent["position"]
    exit_price = price * (1 - slippage(market) if pos["side"] == "LONG" else 1 + slippage(market))
    pnl_ratio = (exit_price - pos["entry"]) / pos["entry"]
    if pos["side"] == "SHORT":
        pnl_ratio = -pnl_ratio

    pnl = agent["capital"] * pos["size"] * pnl_ratio
    fee = abs(pnl) * TAKER_FEE
    agent["capital"] += pnl - fee
    agent["returns"].append(pnl_ratio)

    agent["raw_memory"].append({
        "regime": regime,
        "momentum": round(momentum, 2),
        "pnl": pnl_ratio,
        "timestamp": time.time()
    })
    agent["raw_memory"] = agent["raw_memory"][-RAW_MEMORY_LIMIT:]
    compress_memory(agent)

    agent["position"] = None

# =========================
# Portfolio Risk
# =========================
def portfolio_equity():
    return sum(a["capital"] for a in AGENTS.values() if a["alive"])

def portfolio_returns():
    r = []
    for a in AGENTS.values():
        r.extend(a["returns"][-5:])
    return r

def portfolio_var():
    r = portfolio_returns()
    if len(r) < 5:
        return 0.0
    return abs(statistics.mean(r) - 2 * statistics.stdev(r))

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
        "role": champ["role"],
        "capital": round(champ["capital"], 2),
        "gen": GENERATION
    })
    HALL_OF_FAME.sort(key=lambda x: x["capital"], reverse=True)
    del HALL_OF_FAME[HOF_LIMIT:]

    survivors = ranked[:max(3, len(ranked)//2)]
    AGENTS = {a["id"]: a for a in survivors}

    while len(AGENTS) < POPULATION_SIZE:
        parent = random.choice(survivors)
        g = crossover(champ["gene"], parent["gene"])
        spawn_agent(g, role=parent["role"])

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 49 ONLINE",
        "generation": GENERATION,
        "portfolio_equity": round(portfolio_equity(), 2)
    }

@app.post("/simulate/market")
def simulate(market: MarketInput):
    regime = detect_regime(market)

    var = portfolio_var()
    risk_factor = 1.0
    if var > VAR_LIMIT:
        risk_factor *= RISK_REDUCTION_FACTOR

    if portfolio_equity() < TOTAL_CAPITAL * (1 - PORTFOLIO_MAX_DD):
        for a in AGENTS.values():
            a["position"] = None
        return {"status": "PORTFOLIO KILL SWITCH"}

    for agent in AGENTS.values():
        if agent["position"]:
            close_position(agent, market.price, market, regime, market.momentum)

        decision = decide(agent, market, regime)
        if decision in ["ENTER", "SCALP"]:
            side = "LONG" if regime == "BULL" else "SHORT"
            open_position(agent, side, market.price, position_size(agent, risk_factor), market)

    evolve()

    return {
        "phase": 49,
        "generation": GENERATION,
        "portfolio_var": round(var, 4),
        "agents": len(AGENTS)
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 49,
        "generation": GENERATION,
        "portfolio_equity": portfolio_equity(),
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
