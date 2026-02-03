from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import random
import uuid
import copy
import statistics

app = FastAPI(
    title="ClawBot Phase 47 – Meta Allocator",
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
CRITICAL_DRAWDOWN = 0.20

TAKER_FEE = 0.0006
SLIPPAGE_BASE = 0.0005

MEMORY_LIMIT = 40
HOF_LIMIT = 10

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
        "memory": [],
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
# Meta Allocator (NEW)
# =========================
def regime_weights(regime: str, volatility: str):
    if regime == "BULL":
        return {"TREND": 0.45, "MEAN": 0.15, "SCALP": 0.25, "CRISIS": 0.15}
    if regime == "BEAR":
        return {"TREND": 0.15, "MEAN": 0.20, "SCALP": 0.20, "CRISIS": 0.45}
    # SIDEWAYS
    base = {"TREND": 0.15, "MEAN": 0.45, "SCALP": 0.30, "CRISIS": 0.10}
    if volatility == "high":
        base["SCALP"] += 0.1
        base["MEAN"] -= 0.1
    return base

# =========================
# Memory Engine
# =========================
def similarity(a, b):
    score = 0
    if a["regime"] == b["regime"]:
        score += 0.5
    score += max(0, 0.5 - abs(a["momentum"] - b["momentum"]))
    return score

def memory_bias(agent, snapshot):
    if not agent["memory"]:
        return 0
    weighted = [
        similarity(snapshot, m) * m["pnl"]
        for m in agent["memory"]
    ]
    return sum(weighted) / len(weighted)

# =========================
# Decision Engine
# =========================
def decide(agent, market, regime):
    role = agent["role"]
    mem = memory_bias(agent, {"regime": regime, "momentum": market.momentum})

    if role == "TREND" and abs(market.momentum) > 0.4:
        return "ENTER"
    if role == "MEAN" and regime == "SIDEWAYS":
        return "ENTER"
    if role == "SCALP" and market.volatility == "high":
        return "SCALP"
    if role == "CRISIS" and market.momentum < -0.7:
        return "ENTER"

    if mem > 0.02:
        return "ENTER"

    return "HOLD"

# =========================
# Execution
# =========================
def slippage(market):
    return SLIPPAGE_BASE * {"loose": 0.8, "normal": 1.0, "tight": 1.6}[market.liquidity]

def position_size(agent):
    return max(0.01, min(0.6,
        agent["gene"]["base_position"] * agent["gene"]["risk_tolerance"]
    ))

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
    net = pnl - fee
    agent["capital"] += net
    agent["returns"].append(pnl_ratio)

    agent["memory"].append({
        "regime": regime,
        "momentum": momentum,
        "pnl": pnl_ratio
    })
    agent["memory"] = agent["memory"][-MEMORY_LIMIT:]
    agent["position"] = None

# =========================
# Risk
# =========================
def risk(agent):
    agent["equity"] = agent["capital"]
    agent["peak"] = max(agent["peak"], agent["equity"])
    dd = 1 - agent["equity"] / agent["peak"]

    if dd >= MAX_DRAWDOWN:
        agent["alive"] = False
    elif dd >= CRITICAL_DRAWDOWN and agent["position"]:
        agent["position"]["size"] *= 0.5

# =========================
# Capital Allocation (Meta)
# =========================
def score_agent(agent):
    if len(agent["returns"]) < 3:
        return 0.1
    avg = statistics.mean(agent["returns"])
    vol = statistics.stdev(agent["returns"]) if len(agent["returns"]) > 1 else 0.01
    return max(0.05, avg / max(0.01, vol))

def allocate_capital(regime, volatility):
    alive = [a for a in AGENTS.values() if a["alive"]]
    if not alive:
        return

    weights = regime_weights(regime, volatility)
    role_groups: Dict[str, List[dict]] = {}

    for a in alive:
        role_groups.setdefault(a["role"], []).append(a)

    for role, agents in role_groups.items():
        pool = TOTAL_CAPITAL * weights.get(role, 0.1)
        scores = {a["id"]: score_agent(a) for a in agents}
        total = sum(scores.values()) or 1

        for a in agents:
            a["capital"] = max(
                20_000,
                pool * (scores[a["id"]] / total)
            )

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
        "status": "ClawBot Phase 47 ONLINE",
        "generation": GENERATION,
        "agents": len(AGENTS)
    }

@app.post("/simulate/market")
def simulate(market: MarketInput):
    regime = detect_regime(market)

    for agent in list(AGENTS.values()):
        if not agent["alive"]:
            continue

        decision = decide(agent, market, regime)

        if agent["position"]:
            close_position(agent, market.price, market, regime, market.momentum)

        if decision in ["ENTER", "SCALP"]:
            side = "LONG" if regime == "BULL" else "SHORT"
            open_position(agent, side, market.price, position_size(agent), market)

        risk(agent)

    allocate_capital(regime, market.volatility)
    evolve()

    return {
        "phase": 47,
        "generation": GENERATION,
        "regime": regime,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 47,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "allocator": "META_REGIME"
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
