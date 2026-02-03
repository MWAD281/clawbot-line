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
import threading

app = FastAPI(
    title="ClawBot Phase 50 – Autonomous Live Loop",
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

FORGET_HALF_LIFE = 20
LOOP_INTERVAL = 15  # วินาทีต่อ 1 cycle (ปรับได้)

GENERATION = 1
CYCLE = 0
RUNNING = True

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
# Market Simulator (Internal)
# =========================
def random_market():
    momentum = round(random.uniform(-1, 1), 2)
    return MarketInput(
        volatility=random.choice(["low", "medium", "high"]),
        liquidity=random.choice(["loose", "normal", "tight"]),
        momentum=momentum,
        price=round(100 + random.uniform(-5, 5), 2)
    )

def detect_regime(m):
    if m.momentum > 0.6:
        return "BULL"
    if m.momentum < -0.6:
        return "BEAR"
    return "SIDEWAYS"

# =========================
# Memory Engine
# =========================
def forgetting_weight(age):
    return math.exp(-math.log(2) * age / FORGET_HALF_LIFE)

def compress_memory(agent):
    buckets = {}
    for m in agent["raw_memory"]:
        key = (m["regime"], round(m["momentum"], 1))
        buckets.setdefault(key, []).append(m)

    compressed = []
    for (regime, mom), recs in buckets.items():
        avg_pnl = statistics.mean(r["pnl"] for r in recs)
        compressed.append({
            "regime": regime,
            "momentum": mom,
            "pnl": avg_pnl,
            "count": len(recs),
            "timestamp": max(r["timestamp"] for r in recs)
        })

    compressed.sort(key=lambda x: abs(x["pnl"]), reverse=True)
    agent["compressed_memory"] = compressed[:COMPRESSED_MEMORY_LIMIT]

def memory_bias(agent, regime):
    score = 0.0
    now = time.time()
    for m in agent["compressed_memory"]:
        if m["regime"] != regime:
            continue
        age = now - m["timestamp"]
        score += forgetting_weight(age) * m["pnl"]
    return score

# =========================
# Trading Logic
# =========================
def decide(agent, market, regime):
    bias = memory_bias(agent, regime)
    if bias > 0.015:
        return "ENTER"

    if agent["role"] == "TREND" and abs(market.momentum) > 0.4:
        return "ENTER"
    if agent["role"] == "MEAN" and regime == "SIDEWAYS":
        return "ENTER"
    if agent["role"] == "SCALP" and market.volatility == "high":
        return "SCALP"
    if agent["role"] == "CRISIS" and market.momentum < -0.7:
        return "ENTER"
    return "HOLD"

def slippage(m):
    return SLIPPAGE_BASE * {"loose": 0.8, "normal": 1.0, "tight": 1.6}[m.liquidity]

def position_size(agent, risk_factor):
    return max(0.01, min(0.6, agent["gene"]["base_position"] * agent["gene"]["risk_tolerance"] * risk_factor))

def open_position(agent, side, price, size, market):
    agent["position"] = {"side": side, "entry": price, "size": size}

def close_position(agent, price, regime, momentum):
    pos = agent["position"]
    pnl_ratio = (price - pos["entry"]) / pos["entry"]
    if pos["side"] == "SHORT":
        pnl_ratio = -pnl_ratio

    pnl = agent["capital"] * pos["size"] * pnl_ratio
    agent["capital"] += pnl
    agent["returns"].append(pnl_ratio)

    agent["raw_memory"].append({
        "regime": regime,
        "momentum": momentum,
        "pnl": pnl_ratio,
        "timestamp": time.time()
    })
    agent["raw_memory"] = agent["raw_memory"][-RAW_MEMORY_LIMIT:]
    compress_memory(agent)
    agent["position"] = None

# =========================
# Evolution
# =========================
def evolve():
    global GENERATION, AGENTS
    GENERATION += 1
    ranked = sorted(AGENTS.values(), key=lambda a: a["capital"], reverse=True)

    champ = ranked[0]
    HALL_OF_FAME.append({
        "gene": champ["gene"],
        "capital": round(champ["capital"], 2),
        "gen": GENERATION
    })
    HALL_OF_FAME[:] = sorted(HALL_OF_FAME, key=lambda x: x["capital"], reverse=True)[:HOF_LIMIT]

    survivors = ranked[:max(3, len(ranked)//2)]
    AGENTS.clear()
    for a in survivors:
        AGENTS[a["id"]] = a

    while len(AGENTS) < POPULATION_SIZE:
        p = random.choice(survivors)
        spawn_agent(p["gene"], p["role"])

# =========================
# Autonomous Loop (NEW)
# =========================
def autonomous_loop():
    global CYCLE, RUNNING
    while RUNNING:
        market = random_market()
        regime = detect_regime(market)

        for a in AGENTS.values():
            if a["position"]:
                close_position(a, market.price, regime, market.momentum)

            decision = decide(a, market, regime)
            if decision in ["ENTER", "SCALP"]:
                side = "LONG" if regime == "BULL" else "SHORT"
                open_position(a, side, market.price, position_size(a, 1.0), market)

        evolve()
        CYCLE += 1
        time.sleep(LOOP_INTERVAL)

threading.Thread(target=autonomous_loop, daemon=True).start()

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 50 RUNNING",
        "generation": GENERATION,
        "cycle": CYCLE,
        "agents": len(AGENTS)
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 50,
        "generation": GENERATION,
        "cycle": CYCLE,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
