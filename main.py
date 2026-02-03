from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import random
import uuid
import copy
import statistics

app = FastAPI(
    title="ClawBot Phase 45 – Capital Allocator",
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
POPULATION_SIZE = 6
TOTAL_CAPITAL = 600_000.0
BASE_CAPITAL = TOTAL_CAPITAL / POPULATION_SIZE
MAX_DRAWDOWN = 0.35
CRITICAL_DRAWDOWN = 0.20
TAKER_FEE = 0.0006
SLIPPAGE_BASE = 0.0005
MEMORY_LIMIT = 30
HOF_LIMIT = 8

GENERATION = 1
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []

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
def spawn_agent(parent_gene=None, capital=BASE_CAPITAL):
    aid = str(uuid.uuid4())[:8]
    gene = mutate_gene(parent_gene) if parent_gene else random_gene()
    AGENTS[aid] = {
        "id": aid,
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
# Market
# =========================
def detect_regime(m: MarketInput):
    if m.momentum > 0.4:
        return "BULL"
    if m.momentum < -0.4:
        return "BEAR"
    return "SIDEWAYS"

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
    snapshot = {"regime": regime, "momentum": market.momentum}
    mem = memory_bias(agent, snapshot)
    adapt = agent["gene"]["adaptability"]
    bias = agent["gene"]["trend_bias"].upper()

    if mem > 0.02:
        return "ENTER"
    if mem < -0.02:
        return "HOLD"

    if bias == regime and adapt > 0.4:
        return "ENTER"
    if adapt > 0.7:
        return "SCALP"
    return "HOLD"

# =========================
# Execution
# =========================
def slippage(market):
    return SLIPPAGE_BASE * {"loose": 0.8, "normal": 1.0, "tight": 1.6}[market.liquidity]

def position_size(agent, regime):
    base = agent["gene"]["base_position"]
    risk = agent["gene"]["risk_tolerance"]
    adj = 1.0 if regime != "SIDEWAYS" else 0.6
    return max(0.01, min(0.7, base * risk * adj))

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
# Capital Allocator
# =========================
def score_agent(agent):
    if len(agent["returns"]) < 3:
        return 0
    avg = statistics.mean(agent["returns"])
    vol = statistics.stdev(agent["returns"]) if len(agent["returns"]) > 1 else 0.01
    return avg / max(0.01, vol)

def allocate_capital():
    alive = [a for a in AGENTS.values() if a["alive"]]
    if not alive:
        return

    scores = {a["id"]: max(0, score_agent(a)) for a in alive}
    total_score = sum(scores.values()) or 1

    for a in alive:
        target = TOTAL_CAPITAL * (scores[a["id"]] / total_score)
        a["capital"] = max(10_000, target)

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
        "status": "ClawBot Phase 45 ONLINE",
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
            open_position(agent, side, market.price, position_size(agent, regime), market)

        risk(agent)

    allocate_capital()
    evolve()

    return {
        "phase": 45,
        "generation": GENERATION,
        "regime": regime,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 45,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "allocator": "ACTIVE"
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
