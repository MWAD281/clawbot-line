from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 40 – Capital & Drawdown Engine",
    version="0.6.0"
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
MAX_DRAWDOWN = 0.30   # 30%
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

def mutate_gene(gene):
    g = copy.deepcopy(gene)
    k = random.choice(list(g.keys()))
    g[k] = round(min(1.0, max(0.0, g[k] + random.uniform(-0.15, 0.15))), 2)
    return g

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
        "peak_capital": INITIAL_CAPITAL,
        "pnl": 0.0,
        "alive": True,
        "born_gen": GENERATION
    }

for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Decision Engine
# =========================
def decide(agent, data: MarketInput):
    g = agent["gene"]

    danger = 1 if data.risk_level == "high" else 0
    trend = 1 if data.trend == "up" else -1 if data.trend == "down" else 0

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
# Market PnL Model
# =========================
def market_return(decision: str, data: MarketInput):
    base = random.uniform(-0.01, 0.01)

    if decision == "LONG" and data.trend == "up":
        return abs(base) + 0.01
    if decision == "SHORT" and data.trend == "down":
        return abs(base) + 0.008
    if decision in ["LONG", "SHORT"] and data.trend == "flat":
        return base * 0.5

    return -abs(base) * 1.2

# =========================
# Risk & Drawdown
# =========================
def update_capital(agent, ret):
    size = agent["gene"]["position_size"]
    pnl = agent["capital"] * size * ret

    agent["capital"] += pnl
    agent["pnl"] += pnl
    agent["peak_capital"] = max(agent["peak_capital"], agent["capital"])

    drawdown = 1 - (agent["capital"] / agent["peak_capital"])
    if drawdown >= MAX_DRAWDOWN:
        agent["alive"] = False

    return pnl, drawdown

# =========================
# Hall of Fame
# =========================
def update_hof(champion):
    HALL_OF_FAME.append({
        "gene": champion["gene"],
        "capital": champion["capital"],
        "pnl": champion["pnl"],
        "gen": GENERATION,
        "timestamp": datetime.utcnow().isoformat()
    })
    HALL_OF_FAME.sort(key=lambda x: x["capital"], reverse=True)
    del HALL_OF_FAME[HOF_LIMIT:]

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

    ranked = sorted(alive, key=lambda x: x["capital"], reverse=True)
    champion = ranked[0]
    update_hof(champion)

    survivors = ranked[:max(1, len(ranked)//2)]
    AGENTS = {s["id"]: s for s in survivors}

    while len(AGENTS) < POPULATION_SIZE:
        p1 = champion["gene"]
        p2 = random.choice(
            [s["gene"] for s in survivors] +
            [h["gene"] for h in HALL_OF_FAME]
        )
        spawn_agent(crossover(p1, p2))

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 40 ONLINE",
        "generation": GENERATION,
        "agents": len(AGENTS),
        "hall_of_fame": len(HALL_OF_FAME),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/simulate/market")
def simulate(data: MarketInput):
    cycle = []

    for agent in AGENTS.values():
        if not agent["alive"]:
            continue

        decision = decide(agent, data)
        ret = market_return(decision, data)
        pnl, dd = update_capital(agent, ret)

        cycle.append({
            "agent_id": agent["id"],
            "decision": decision,
            "return": round(ret, 5),
            "pnl": round(pnl, 2),
            "capital": round(agent["capital"], 2),
            "drawdown": round(dd, 3),
            "alive": agent["alive"]
        })

    evolve()

    MEMORY.append({
        "gen": GENERATION,
        "input": data.dict(),
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "engine": "ClawBot Phase 40",
        "generation": GENERATION,
        "cycle": cycle,
        "agents_alive": len([a for a in AGENTS.values() if a["alive"]])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 40,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "memory": len(MEMORY),
        "status": "CAPITAL_AWARE",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
