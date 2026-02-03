from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 41 – Risk Manager AI",
    version="0.7.0"
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
    risk_level: str
    trend: str
    volatility: str
    liquidity: str

# =========================
# Global State
# =========================
POPULATION_SIZE = 4
INITIAL_CAPITAL = 100_000.0
MAX_DRAWDOWN = 0.30
CRITICAL_DRAWDOWN = 0.20
HOF_LIMIT = 5

GENERATION = 1
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []
MEMORY: List[dict] = []

# =========================
# Genetics
# =========================
def random_gene():
    return {
        "aggression": round(random.uniform(0.0, 1.0), 2),
        "risk_tolerance": round(random.uniform(0.0, 1.0), 2),
        "reactivity": round(random.uniform(0.0, 1.0), 2),
        "position_size": round(random.uniform(0.1, 1.0), 2)
    }

def mutate_gene(g):
    g2 = copy.deepcopy(g)
    k = random.choice(list(g2.keys()))
    g2[k] = round(min(1.0, max(0.0, g2[k] + random.uniform(-0.2, 0.2))), 2)
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
        "pnl": 0.0,
        "alive": True,
        "risk_blocked": False,
        "born_gen": GENERATION
    }

for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Decision Engine
# =========================
def decide(agent, market: MarketInput):
    g = agent["gene"]
    danger = 1 if market.risk_level == "high" else 0
    trend = 1 if market.trend == "up" else -1 if market.trend == "down" else 0

    score = (
        g["aggression"] * trend +
        g["reactivity"] * trend -
        danger * (1 - g["risk_tolerance"])
    )

    if score > 0.4:
        return "LONG"
    if score < -0.4:
        return "SHORT"
    return "FLAT"

# =========================
# Market Return
# =========================
def market_return(decision, market):
    base = random.uniform(-0.01, 0.01)

    if decision == "LONG" and market.trend == "up":
        return abs(base) + 0.01
    if decision == "SHORT" and market.trend == "down":
        return abs(base) + 0.008
    if decision in ["LONG", "SHORT"] and market.trend == "flat":
        return base * 0.4

    return -abs(base) * 1.2

# =========================
# Risk Manager Agent
# =========================
def risk_manager(agent):
    drawdown = 1 - (agent["capital"] / agent["peak"])

    action = "ALLOW"

    if drawdown >= CRITICAL_DRAWDOWN:
        agent["gene"]["position_size"] = round(
            max(0.05, agent["gene"]["position_size"] * 0.5), 2
        )
        action = "REDUCE_SIZE"

    if drawdown >= MAX_DRAWDOWN:
        agent["alive"] = False
        agent["risk_blocked"] = True
        action = "KILL_AGENT"

    return action, round(drawdown, 3)

# =========================
# Capital Update
# =========================
def apply_pnl(agent, ret):
    size = agent["gene"]["position_size"]
    pnl = agent["capital"] * size * ret

    agent["capital"] += pnl
    agent["pnl"] += pnl
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
        g2 = random.choice(
            [s["gene"] for s in survivors] +
            [h["gene"] for h in HALL_OF_FAME]
        )
        spawn_agent(crossover(g1, g2))

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 41 ONLINE",
        "generation": GENERATION,
        "agents": len(AGENTS),
        "hof": len(HALL_OF_FAME),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/simulate/market")
def simulate(market: MarketInput):
    cycle = []

    for agent in AGENTS.values():
        if not agent["alive"]:
            continue

        decision = decide(agent, market)
        ret = market_return(decision, market)
        pnl = apply_pnl(agent, ret)

        risk_action, dd = risk_manager(agent)

        cycle.append({
            "agent": agent["id"],
            "decision": decision,
            "return": round(ret, 5),
            "pnl": round(pnl, 2),
            "capital": round(agent["capital"], 2),
            "drawdown": dd,
            "risk_action": risk_action,
            "alive": agent["alive"]
        })

    evolve()

    MEMORY.append({
        "gen": GENERATION,
        "market": market.dict(),
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "phase": 41,
        "generation": GENERATION,
        "cycle": cycle,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 41,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "memory": len(MEMORY),
        "status": "RISK_MANAGED"
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
