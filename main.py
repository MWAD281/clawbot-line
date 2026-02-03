from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 42 – Multi Market Darwinism",
    version="0.8.0"
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
    momentum: float  # -1.0 ถึง +1.0

# =========================
# Global Config
# =========================
POPULATION_SIZE = 5
INITIAL_CAPITAL = 100_000.0
MAX_DRAWDOWN = 0.35
CRITICAL_DRAWDOWN = 0.20
HOF_LIMIT = 6

GENERATION = 1
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []
MEMORY: List[dict] = []

# =========================
# Genetics
# =========================
def random_gene():
    return {
        "aggression": round(random.uniform(0, 1), 2),
        "risk_tolerance": round(random.uniform(0, 1), 2),
        "adaptability": round(random.uniform(0, 1), 2),
        "position_size": round(random.uniform(0.1, 1.0), 2),
        "trend_bias": random.choice(["bull", "bear", "neutral"])
    }

def mutate_gene(g):
    g2 = copy.deepcopy(g)
    key = random.choice(list(g2.keys()))
    if isinstance(g2[key], float):
        g2[key] = round(min(1.0, max(0.0, g2[key] + random.uniform(-0.2, 0.2))), 2)
    elif isinstance(g2[key], str):
        g2[key] = random.choice(["bull", "bear", "neutral"])
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
        "peak": INITIAL_CAPITAL,
        "alive": True,
        "born_gen": GENERATION
    }

for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Market Regime Detector
# =========================
def detect_regime(market: MarketInput):
    if market.momentum > 0.4:
        return "BULL"
    if market.momentum < -0.4:
        return "BEAR"
    return "SIDEWAYS"

# =========================
# Decision Engine
# =========================
def decide(agent, regime):
    bias = agent["gene"]["trend_bias"]
    adapt = agent["gene"]["adaptability"]

    if bias.upper() == regime:
        return "TRADE"
    if adapt > 0.7:
        return "ADAPT"
    return "HOLD"

# =========================
# Market Return Engine
# =========================
def market_return(regime, decision):
    base = random.uniform(-0.01, 0.01)

    if decision == "TRADE":
        if regime == "BULL":
            return abs(base) + 0.015
        if regime == "BEAR":
            return abs(base) + 0.012
        return base * 0.4

    if decision == "ADAPT":
        return base * 0.3

    return -abs(base) * 0.6

# =========================
# Risk Manager
# =========================
def risk_manager(agent):
    dd = 1 - (agent["capital"] / agent["peak"])

    action = "ALLOW"

    if dd >= CRITICAL_DRAWDOWN:
        agent["gene"]["position_size"] = round(
            max(0.05, agent["gene"]["position_size"] * 0.5), 2
        )
        action = "REDUCE"

    if dd >= MAX_DRAWDOWN:
        agent["alive"] = False
        action = "KILL"

    return action, round(dd, 3)

# =========================
# Capital Update
# =========================
def apply_pnl(agent, ret):
    size = agent["gene"]["position_size"]
    pnl = agent["capital"] * size * ret

    agent["capital"] += pnl
    agent["peak"] = max(agent["peak"], agent["capital"])
    return pnl

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
    champion = ranked[0]

    HALL_OF_FAME.append({
        "gene": champion["gene"],
        "capital": champion["capital"],
        "gen": GENERATION
    })
    HALL_OF_FAME.sort(key=lambda x: x["capital"], reverse=True)
    del HALL_OF_FAME[HOF_LIMIT:]

    survivors = ranked[:max(1, len(ranked)//2)]
    AGENTS = {a["id"]: a for a in survivors}

    while len(AGENTS) < POPULATION_SIZE:
        g1 = champion["gene"]
        g2 = random.choice([s["gene"] for s in survivors])
        spawn_agent(crossover(g1, g2))

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 42 ONLINE",
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
        ret = market_return(regime, decision)
        pnl = apply_pnl(agent, ret)
        risk_action, dd = risk_manager(agent)

        cycle.append({
            "agent": agent["id"],
            "decision": decision,
            "regime": regime,
            "pnl": round(pnl, 2),
            "capital": round(agent["capital"], 2),
            "drawdown": dd,
            "risk_action": risk_action,
            "alive": agent["alive"]
        })

    evolve()

    MEMORY.append({
        "gen": GENERATION,
        "regime": regime,
        "market": market.dict(),
        "cycle": cycle
    })

    return {
        "phase": 42,
        "generation": GENERATION,
        "regime": regime,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]]),
        "cycle": cycle
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 42,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "memory": len(MEMORY),
        "status": "MULTI_MARKET_ACTIVE"
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
