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

app = FastAPI(title="ClawBot Phase 32 – Regime-Aware Darwinism")

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

POPULATION_SIZE = 10
INITIAL_CASH = 100_000
EXTINCTION_LEVEL = 0.5
MUTATION_RATE = 0.28
MEMORY_DECAY = 0.90
WORLD_PRESSURE_GROWTH = 1.12

# ==================================================
# WORLD STATE
# ==================================================

WORLD = {
    "epoch": 0,
    "generation": 1,
    "pressure": 1.0,
    "regime": "NEUTRAL",
    "agents": [],
    "lineages": [],
    "graveyard": []
}

# ==================================================
# DNA / LINEAGE
# ==================================================

def random_dna():
    return {
        "risk": round(random.uniform(0.01, 0.06), 3),
        "leverage": round(random.uniform(1.0, 4.0), 2),
        "aggression": round(random.uniform(0.2, 1.0), 2),
        "discipline": round(random.uniform(0.3, 0.9), 2),
        "regime_bias": random.choice(["RISK_ON", "RISK_OFF", "VOLATILE"])
    }

def mutate_dna(dna):
    d = dna.copy()
    for k in d:
        if random.random() < MUTATION_RATE:
            if isinstance(d[k], float):
                d[k] = round(max(0.01, d[k] + random.uniform(-0.12, 0.12)), 3)
            elif isinstance(d[k], str):
                d[k] = random.choice(["RISK_ON", "RISK_OFF", "VOLATILE"])
    return d

def new_memory():
    return {
        "confidence": 0.5,
        "trauma": 0.0,
        "adaptation": 0.5
    }

# ==================================================
# AGENT
# ==================================================

def spawn_agent(dna=None, lineage=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": INITIAL_CASH,
        "peak": INITIAL_CASH,
        "dna": dna or random_dna(),
        "memory": new_memory(),
        "lineage": lineage or uuid.uuid4().hex[:6],
        "last_pnl": 0.0
    }

def reset_population(seed_agent):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        WORLD["agents"].append(
            spawn_agent(
                dna=mutate_dna(seed_agent["dna"]),
                lineage=seed_agent["lineage"]
            )
        )

# ==================================================
# REGIME ENGINE
# ==================================================

def infer_regime(market: Dict):
    if market.get("volatility", 1) > 1.5:
        return "VOLATILE"
    if market.get("trend") == "up":
        return "RISK_ON"
    if market.get("trend") == "down":
        return "RISK_OFF"
    return "NEUTRAL"

# ==================================================
# FITNESS
# ==================================================

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    mem = a["memory"]
    return a["equity"] * (1 - dd) * (1 - mem["trauma"]) * mem["confidence"]

# ==================================================
# SIMULATION CORE
# ==================================================

def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    dna = agent["dna"]
    mem = agent["memory"]

    regime_match = 1.2 if dna["regime_bias"] == WORLD["regime"] else 0.8
    volatility = market.get("volatility", 1.0)

    edge = random.uniform(-1, 1)

    pnl = (
        agent["equity"]
        * dna["risk"]
        * dna["leverage"]
        * dna["aggression"]
        * regime_match
        * volatility
        * WORLD["pressure"]
        * edge
    )

    pnl *= (1 - dna["discipline"] * mem["trauma"])

    agent["equity"] += pnl
    agent["last_pnl"] = pnl

    if pnl > 0:
        mem["confidence"] = min(1.0, mem["confidence"] + 0.06)
        mem["adaptation"] = min(1.0, mem["adaptation"] + 0.04)
    else:
        mem["trauma"] = min(1.0, mem["trauma"] + 0.1)
        mem["confidence"] = max(0.0, mem["confidence"] - 0.08)

    mem["trauma"] *= MEMORY_DECAY

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < INITIAL_CASH * EXTINCTION_LEVEL:
        agent["alive"] = False
        WORLD["graveyard"].append(agent)

# ==================================================
# EVOLUTION
# ==================================================

def evolve():
    alive = [a for a in WORLD["agents"] if a["alive"]]

    if len(alive) <= 3:
        champion = max(WORLD["agents"], key=fitness)

        WORLD["lineages"].append({
            "gen": WORLD["generation"],
            "id": champion["id"],
            "lineage": champion["lineage"],
            "equity": round(champion["equity"], 2),
            "dna": champion["dna"]
        })

        WORLD["generation"] += 1
        WORLD["pressure"] *= WORLD_PRESSURE_GROWTH
        reset_population(champion)

# ==================================================
# API
# ==================================================

@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["epoch"] += 1
    WORLD["regime"] = infer_regime(market)

    for a in WORLD["agents"]:
        simulate_agent(a, market)

    evolve()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "regime": WORLD["regime"],
        "pressure": round(WORLD["pressure"], 3),
        "champion": champion["id"],
        "agents": [
            {
                "id": a["id"],
                "eq": round(a["equity"], 2),
                "alive": a["alive"],
                "conf": round(a["memory"]["confidence"], 2),
                "trauma": round(a["memory"]["trauma"], 2),
                "lineage": a["lineage"]
            } for a in WORLD["agents"]
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 32 ONLINE",
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "regime": WORLD["regime"],
        "pressure": round(WORLD["pressure"], 3),
        "graveyard": len(WORLD["graveyard"]),
        "lineages": len(WORLD["lineages"])
    }

@app.get("/lineages")
def lineages():
    return WORLD["lineages"][-10:]

# ==================================================
# INIT
# ==================================================

seed = spawn_agent()
WORLD["agents"] = [seed]
reset_population(seed)
