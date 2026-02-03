from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import time
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 31 – Autonomous Meta-Evolution")

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

POPULATION_SIZE = 8
INITIAL_CASH = 100_000
EXTINCTION_THRESHOLD = 0.55
MUTATION_RATE = 0.3
MEMORY_DECAY = 0.92
META_PRESSURE = 1.15  # โลกโหดขึ้นเรื่อย ๆ

# ==================================================
# WORLD
# ==================================================

WORLD: Dict = {
    "epoch": 0,
    "generation": 1,
    "difficulty": 1.0,
    "market": {},
    "agents": [],
    "graveyard": [],
    "hall_of_fame": []
}

# ==================================================
# DNA / MEMORY
# ==================================================

def random_dna():
    return {
        "risk": round(random.uniform(0.01, 0.06), 3),
        "leverage": round(random.uniform(1.0, 4.0), 2),
        "aggression": round(random.uniform(0.2, 1.0), 2),
        "vol_bias": random.choice(["low", "mid", "high"]),
        "discipline": round(random.uniform(0.3, 0.9), 2)
    }

def mutate_dna(dna):
    d = dna.copy()
    for k in d:
        if random.random() < MUTATION_RATE:
            if isinstance(d[k], float):
                d[k] = round(max(0.01, d[k] + random.uniform(-0.15, 0.15)), 3)
    return d

def new_memory():
    return {
        "wins": 0,
        "losses": 0,
        "trauma": 0.0,
        "confidence": 0.5
    }

# ==================================================
# AGENT
# ==================================================

def spawn_agent(dna=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": INITIAL_CASH,
        "peak": INITIAL_CASH,
        "dna": dna or random_dna(),
        "memory": new_memory(),
        "last_pnl": 0.0
    }

def reset_population(seed=None):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        if seed:
            WORLD["agents"].append(spawn_agent(mutate_dna(seed)))
        else:
            WORLD["agents"].append(spawn_agent())

# ==================================================
# FITNESS
# ==================================================

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    trauma_penalty = 1 - a["memory"]["trauma"]
    return a["equity"] * trauma_penalty * (1 - dd)

# ==================================================
# SIMULATION
# ==================================================

def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    dna = agent["dna"]
    mem = agent["memory"]

    vol_factor = {"low": 0.5, "mid": 1.0, "high": 1.6}[dna["vol_bias"]]
    market_vol = market.get("volatility", 1.0)

    edge = random.uniform(-1, 1)
    pnl = (
        agent["equity"]
        * dna["risk"]
        * dna["leverage"]
        * dna["aggression"]
        * vol_factor
        * market_vol
        * WORLD["difficulty"]
        * edge
    )

    pnl *= (1 - dna["discipline"] * mem["trauma"])

    agent["equity"] += pnl
    agent["last_pnl"] = pnl

    if pnl > 0:
        mem["wins"] += 1
        mem["confidence"] = min(1.0, mem["confidence"] + 0.05)
    else:
        mem["losses"] += 1
        mem["trauma"] = min(1.0, mem["trauma"] + 0.08)
        mem["confidence"] = max(0.0, mem["confidence"] - 0.07)

    mem["trauma"] *= MEMORY_DECAY

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < INITIAL_CASH * EXTINCTION_THRESHOLD:
        agent["alive"] = False
        WORLD["graveyard"].append(agent)

# ==================================================
# EVOLUTION
# ==================================================

def evolution():
    alive = [a for a in WORLD["agents"] if a["alive"]]

    if len(alive) <= 2:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["hall_of_fame"].append({
            "gen": WORLD["generation"],
            "id": champion["id"],
            "equity": round(champion["equity"], 2),
            "dna": champion["dna"]
        })

        WORLD["generation"] += 1
        WORLD["difficulty"] *= META_PRESSURE
        reset_population(seed=champion["dna"])

# ==================================================
# API
# ==================================================

@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["epoch"] += 1
    WORLD["market"] = market

    for a in WORLD["agents"]:
        simulate_agent(a, market)

    evolution()

    champ = max(WORLD["agents"], key=fitness)

    return {
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "difficulty": round(WORLD["difficulty"], 3),
        "champion": champ["id"],
        "agents": [
            {
                "id": a["id"],
                "eq": round(a["equity"], 2),
                "alive": a["alive"],
                "conf": round(a["memory"]["confidence"], 2),
                "trauma": round(a["memory"]["trauma"], 2),
                "gen": a["generation"]
            } for a in WORLD["agents"]
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 31 ONLINE",
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "difficulty": round(WORLD["difficulty"], 3),
        "graveyard": len(WORLD["graveyard"]),
        "hall_of_fame": len(WORLD["hall_of_fame"])
    }

@app.get("/hall_of_fame")
def hof():
    return WORLD["hall_of_fame"][-10:]

# ==================================================
# INIT
# ==================================================

reset_population()
