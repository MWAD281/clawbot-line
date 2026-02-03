from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 39 – Champion & Hall of Fame",
    version="0.5.0"
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
# Core State
# =========================
AGENTS: Dict[str, dict] = {}
HALL_OF_FAME: List[dict] = []
MEMORY: List[dict] = []
GENERATION = 1
POPULATION_SIZE = 4
HOF_LIMIT = 5

# =========================
# Genetics
# =========================
def random_gene():
    return {
        "aggression": round(random.uniform(0.0, 1.0), 2),
        "risk_tolerance": round(random.uniform(0.0, 1.0), 2),
        "reactivity": round(random.uniform(0.0, 1.0), 2),
    }

def mutate_gene(gene):
    g = copy.deepcopy(gene)
    k = random.choice(list(g.keys()))
    g[k] = min(1.0, max(0.0, g[k] + random.uniform(-0.15, 0.15)))
    return g

def crossover(g1, g2):
    return {
        k: round(random.choice([g1[k], g2[k]]), 2)
        for k in g1
    }

# =========================
# Agent Factory
# =========================
def spawn_agent(parent_gene=None):
    agent_id = str(uuid.uuid4())[:8]
    gene = mutate_gene(parent_gene) if parent_gene else random_gene()

    AGENTS[agent_id] = {
        "id": agent_id,
        "gene": gene,
        "score": 0.0,
        "born_gen": GENERATION,
        "alive": True
    }

# Initial population
for _ in range(POPULATION_SIZE):
    spawn_agent()

# =========================
# Decision Engine
# =========================
def agent_decision(agent, data: MarketInput):
    g = agent["gene"]

    danger = 1 if data.risk_level == "high" else 0
    trend = 1 if data.trend == "up" else -1 if data.trend == "down" else 0

    score = (
        g["aggression"] * trend +
        g["reactivity"] * trend -
        danger * (1 - g["risk_tolerance"])
    )

    if score > 0.4:
        return "AGGRESSIVE"
    if score < -0.4:
        return "DEFENSIVE"
    return "HOLD"

# =========================
# Reward Function
# =========================
def evaluate(decision: str, data: MarketInput):
    if decision == "AGGRESSIVE" and data.trend == "up":
        return +1.5
    if decision == "DEFENSIVE" and data.trend == "down":
        return +1.2
    if decision == "AGGRESSIVE" and data.trend == "down":
        return -2.0
    return -0.2

# =========================
# Champion Logic
# =========================
def update_hall_of_fame(champion):
    entry = {
        "gene": champion["gene"],
        "score": champion["score"],
        "gen": GENERATION,
        "timestamp": datetime.utcnow().isoformat()
    }
    HALL_OF_FAME.append(entry)
    HALL_OF_FAME.sort(key=lambda x: x["score"], reverse=True)
    del HALL_OF_FAME[HOF_LIMIT:]

# =========================
# Evolution Cycle
# =========================
def evolution_cycle():
    global GENERATION, AGENTS
    GENERATION += 1

    ranked = sorted(AGENTS.values(), key=lambda x: x["score"], reverse=True)
    champion = ranked[0]
    update_hall_of_fame(champion)

    survivors = ranked[:max(1, len(ranked)//2)]
    AGENTS = {}

    # survivors stay
    for s in survivors:
        AGENTS[s["id"]] = s

    # breed from champion + survivors / hof
    while len(AGENTS) < POPULATION_SIZE:
        parent1 = champion["gene"]
        parent2 = random.choice(
            [s["gene"] for s in survivors] +
            [h["gene"] for h in HALL_OF_FAME]
        )
        child_gene = crossover(parent1, parent2)
        spawn_agent(child_gene)

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 39 ONLINE",
        "generation": GENERATION,
        "agents": len(AGENTS),
        "hall_of_fame": len(HALL_OF_FAME),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    cycle = []

    for agent in AGENTS.values():
        decision = agent_decision(agent, data)
        reward = evaluate(decision, data)
        agent["score"] += reward

        cycle.append({
            "agent_id": agent["id"],
            "decision": decision,
            "reward": reward,
            "score": agent["score"],
            "gene": agent["gene"]
        })

    evolution_cycle()

    MEMORY.append({
        "gen": GENERATION,
        "input": data.dict(),
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "engine": "ClawBot Phase 39",
        "generation": GENERATION,
        "cycle": cycle,
        "agents_alive": len(AGENTS)
    }

@app.get("/dashboard")
def dashboard():
    return {
        "phase": 39,
        "generation": GENERATION,
        "agents": list(AGENTS.values()),
        "hall_of_fame": HALL_OF_FAME,
        "memory_size": len(MEMORY),
        "status": "CHAMPION_TRACKING",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
