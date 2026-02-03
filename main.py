from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid

app = FastAPI(title="ClawBot Phase 29 – Darwinian Multiverse")

# ==================================================
# CORS
# ==================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# CONFIG
# ==================================================
MAX_WORLDS = 4
POPULATION = 15
BASE_CAPITAL = 100_000
EXTINCTION_LEVEL = 0.4

WORLD_TYPES = ["crypto", "equity", "macro"]
TRENDS = ["up", "down", "side"]
GOALS = ["GROWTH", "SURVIVAL", "DOMINANCE"]

# ==================================================
# DNA
# ==================================================
def strategy_gene():
    return {
        "risk": round(random.uniform(0.01, 0.25), 3),
        "leverage": round(random.uniform(1, 15), 2),
        "aggression": round(random.uniform(0.2, 3.0), 2),
    }

def meta_gene():
    return {
        "mutation_rate": round(random.uniform(0.2, 0.9), 2),
        "adaptivity": round(random.uniform(0.2, 2.0), 2),
        "chaos": round(random.uniform(0.0, 2.0), 2),
    }

def random_dna():
    return {
        "strategy": {
            w: {t: strategy_gene() for t in TRENDS}
            for w in WORLD_TYPES
        },
        "meta": meta_gene()
    }

def mutate_dna(dna):
    new = {"strategy": {}, "meta": dna["meta"].copy()}
    m = new["meta"]

    for k in m:
        if random.random() < 0.4:
            m[k] = round(max(0.1, min(2.5, m[k] + random.uniform(-0.3, 0.3))), 2)

    for w in dna["strategy"]:
        new["strategy"][w] = {}
        for t in dna["strategy"][w]:
            g = dna["strategy"][w][t].copy()
            if random.random() < m["mutation_rate"]:
                g["risk"] = round(max(0.005, min(0.4, g["risk"] + random.uniform(-0.05, 0.05))), 3)
            if random.random() < m["mutation_rate"]:
                g["leverage"] = round(max(1, min(25, g["leverage"] + random.uniform(-4, 4))), 2)
            if random.random() < m["mutation_rate"]:
                g["aggression"] = round(max(0.1, min(4.0, g["aggression"] + random.uniform(-0.7, 0.7))), 2)
            new["strategy"][w][t] = g

    return new

# ==================================================
# AGENT
# ==================================================
def spawn_agent(dna=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "alive": True,
        "equity": BASE_CAPITAL,
        "peak": BASE_CAPITAL,
        "dna": dna or random_dna(),
        "goal": random.choice(GOALS),
        "score": 0.0,
        "age": 0,
    }

def fitness(agent):
    dd = (agent["peak"] - agent["equity"]) / max(agent["peak"], 1)
    if agent["goal"] == "SURVIVAL":
        return agent["equity"] * (1 - dd * 2)
    if agent["goal"] == "DOMINANCE":
        return agent["score"]
    return agent["equity"]

# ==================================================
# WORLD
# ==================================================
def spawn_world(parent_dna=None):
    return {
        "id": uuid.uuid4().hex[:6],
        "age": 0,
        "law": {
            "tax": round(random.uniform(0.01, 0.05), 3),
        },
        "culture": {
            "dominant_goal": random.choice(GOALS)
        },
        "agents": [
            spawn_agent(mutate_dna(parent_dna) if parent_dna else None)
            for _ in range(POPULATION)
        ],
        "alive": True,
        "score": 0.0
    }

# ==================================================
# MULTIVERSE
# ==================================================
MULTIVERSE: List[Dict] = [spawn_world() for _ in range(2)]
STEP = 0

# ==================================================
# SIMULATION
# ==================================================
def adapt_goal(agent):
    if agent["equity"] < BASE_CAPITAL * 0.7:
        agent["goal"] = "SURVIVAL"
    elif agent["score"] > BASE_CAPITAL * 0.6:
        agent["goal"] = "DOMINANCE"
    elif agent["equity"] > agent["peak"] * 1.2:
        agent["goal"] = "GROWTH"

def simulate_agent(agent, market, world):
    if not agent["alive"]:
        return

    agent["age"] += 1
    g = agent["dna"]["strategy"][market["world"]][market["trend"]]
    m = agent["dna"]["meta"]

    edge = random.uniform(-1, 1)
    chaos = random.uniform(-1, 1) * m["chaos"]

    intent = 1.0
    if agent["goal"] == "SURVIVAL":
        intent = 0.6
    elif agent["goal"] == "DOMINANCE":
        intent = 1.4

    pnl = agent["equity"] * g["risk"] * g["leverage"] * g["aggression"] * intent * (edge + chaos) * 0.01
    tax = abs(pnl) * world["law"]["tax"]

    agent["equity"] += pnl - tax
    agent["score"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_LEVEL:
        agent["alive"] = False

    adapt_goal(agent)

def simulate_world(world, market):
    if not world["alive"]:
        return

    world["age"] += 1

    for a in world["agents"]:
        simulate_agent(a, market, world)

    alive = [a for a in world["agents"] if a["alive"]]
    if not alive:
        world["alive"] = False
        return

    champ = max(alive, key=fitness)
    world["culture"]["dominant_goal"] = champ["goal"]
    world["score"] = sum(a["equity"] for a in alive)

# ==================================================
# WORLD EVOLUTION
# ==================================================
def evolve_multiverse():
    global MULTIVERSE

    alive_worlds = [w for w in MULTIVERSE if w["alive"]]

    if len(alive_worlds) == 0:
        MULTIVERSE = [spawn_world()]
        return

    if len(alive_worlds) < MAX_WORLDS:
        parent = max(alive_worlds, key=lambda w: w["score"])
        champ = max(parent["agents"], key=fitness)
        MULTIVERSE.append(spawn_world(parent_dna=champ["dna"]))

    if len(alive_worlds) > 1:
        worst = min(alive_worlds, key=lambda w: w["score"])
        if worst["score"] < BASE_CAPITAL * POPULATION * 0.3:
            worst["alive"] = False

# ==================================================
# API
# ==================================================
@app.post("/simulate/market")
def simulate_market(market: Dict):
    global STEP
    STEP += 1

    for w in MULTIVERSE:
        simulate_world(w, market)

    evolve_multiverse()

    return {
        "step": STEP,
        "worlds": [
            {
                "id": w["id"],
                "alive": w["alive"],
                "age": w["age"],
                "score": round(w["score"], 2),
                "culture": w["culture"],
                "agents_alive": len([a for a in w["agents"] if a["alive"]]),
            }
            for w in MULTIVERSE
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 29 online",
        "step": STEP,
        "worlds": len(MULTIVERSE),
    }

@app.get("/dashboard")
def dashboard():
    return {
        "step": STEP,
        "multiverse": MULTIVERSE
    }
