from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 34 – Strategic Memory Engine")

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

POPULATION_SIZE = 14
INITIAL_CASH = 100_000
EXTINCTION_LEVEL = 0.42
MUTATION_RATE = 0.28
PRESSURE_GROWTH = 1.12

MARKETS = ["EQUITY", "CRYPTO", "COMMODITY"]

# ==================================================
# WORLD
# ==================================================

WORLD = {
    "epoch": 0,
    "generation": 1,
    "pressure": 1.0,
    "active_market": "EQUITY",
    "agents": [],
    "lineages": [],
    "extinctions": [],
    "deception_level": 0.0
}

# ==================================================
# DNA
# ==================================================

def random_dna():
    return {
        "risk": round(random.uniform(0.01, 0.06), 3),
        "leverage": round(random.uniform(1.0, 4.0), 2),
        "aggression": round(random.uniform(0.2, 1.0), 2),
        "discipline": round(random.uniform(0.3, 0.95), 2),
        "market_bias": random.choice(MARKETS),
        "regime_bias": random.choice(["RISK_ON", "RISK_OFF", "VOLATILE"]),
        "memory_weight": round(random.uniform(0.2, 0.9), 2)
    }

def mutate_dna(dna):
    d = dna.copy()
    for k in d:
        if random.random() < MUTATION_RATE:
            if isinstance(d[k], float):
                d[k] = round(max(0.01, d[k] + random.uniform(-0.15, 0.15)), 3)
            elif isinstance(d[k], str):
                d[k] = random.choice(MARKETS if k == "market_bias" else ["RISK_ON", "RISK_OFF", "VOLATILE"])
    return d

# ==================================================
# AGENT
# ==================================================

def spawn_agent(dna=None, inherited_memory=None, lineage=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": INITIAL_CASH,
        "peak": INITIAL_CASH,
        "dna": dna or random_dna(),
        "memory": inherited_memory or {
            "confidence": 0.5,
            "trauma": 0.0,
            "regime_fear": {},
            "market_fear": {}
        },
        "lineage": lineage or uuid.uuid4().hex[:6],
        "last_pnl": 0.0,
        "age": 0
    }

def reset_population(champion):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        WORLD["agents"].append(
            spawn_agent(
                dna=mutate_dna(champion["dna"]),
                inherited_memory=copy.deepcopy(champion["memory"]),
                lineage=champion["lineage"]
            )
        )

# ==================================================
# REGIME / DECEPTION
# ==================================================

def infer_regime(market):
    if market["volatility"] > 1.5:
        return "VOLATILE"
    if market["trend"] == "up":
        return "RISK_ON"
    if market["trend"] == "down":
        return "RISK_OFF"
    return "NEUTRAL"

def apply_deception(market):
    if random.random() < WORLD["deception_level"]:
        market = market.copy()
        market["trend"] = random.choice(["up", "down"])
        market["volatility"] *= random.uniform(0.3, 0.7)
    return market

# ==================================================
# FITNESS
# ==================================================

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    survival_bonus = min(1.3, 1 + a["age"] * 0.02)
    return a["equity"] * (1 - dd) * a["memory"]["confidence"] * survival_bonus

# ==================================================
# SIMULATION
# ==================================================

def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    dna = agent["dna"]
    mem = agent["memory"]
    agent["age"] += 1

    regime_penalty = mem["regime_fear"].get(market["regime"], 0)
    market_penalty = mem["market_fear"].get(WORLD["active_market"], 0)

    edge = random.uniform(-1, 1)

    pnl = (
        agent["equity"]
        * dna["risk"]
        * dna["leverage"]
        * dna["aggression"]
        * market["volatility"]
        * WORLD["pressure"]
        * edge
    )

    pnl *= (1 - dna["memory_weight"] * (regime_penalty + market_penalty))
    pnl *= (1 - dna["discipline"] * mem["trauma"])

    agent["equity"] += pnl
    agent["last_pnl"] = pnl

    if pnl > 0:
        mem["confidence"] = min(1.0, mem["confidence"] + 0.04)
    else:
        mem["trauma"] = min(1.0, mem["trauma"] + 0.1)
        mem["confidence"] = max(0.0, mem["confidence"] - 0.06)
        mem["regime_fear"][market["regime"]] = mem["regime_fear"].get(market["regime"], 0) + 0.1
        mem["market_fear"][WORLD["active_market"]] = mem["market_fear"].get(WORLD["active_market"], 0) + 0.1

    mem["trauma"] *= 0.9

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < INITIAL_CASH * EXTINCTION_LEVEL:
        agent["alive"] = False

# ==================================================
# EVOLUTION
# ==================================================

def evolve():
    alive = [a for a in WORLD["agents"] if a["alive"]]

    if len(alive) <= 4:
        champion = max(WORLD["agents"], key=fitness)

        WORLD["lineages"].append({
            "gen": WORLD["generation"],
            "id": champion["id"],
            "equity": round(champion["equity"], 2),
            "dna": champion["dna"]
        })

        WORLD["extinctions"].append({
            "gen": WORLD["generation"],
            "pressure": round(WORLD["pressure"], 2),
            "deception": round(WORLD["deception_level"], 2)
        })

        WORLD["generation"] += 1
        WORLD["pressure"] *= PRESSURE_GROWTH
        WORLD["deception_level"] = min(0.6, WORLD["deception_level"] + 0.05)

        reset_population(champion)

# ==================================================
# API
# ==================================================

@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["epoch"] += 1

    WORLD["active_market"] = market.get("market", random.choice(MARKETS))
    market["regime"] = infer_regime(market)
    market = apply_deception(market)

    for a in WORLD["agents"]:
        simulate_agent(a, market)

    evolve()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "market": WORLD["active_market"],
        "regime": market["regime"],
        "pressure": round(WORLD["pressure"], 2),
        "deception": round(WORLD["deception_level"], 2),
        "champion": champion["id"],
        "agents": [
            {
                "id": a["id"],
                "eq": round(a["equity"], 2),
                "alive": a["alive"],
                "age": a["age"],
                "conf": round(a["memory"]["confidence"], 2),
                "lineage": a["lineage"]
            } for a in WORLD["agents"]
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 34 ONLINE",
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "pressure": round(WORLD["pressure"], 2),
        "deception": round(WORLD["deception_level"], 2)
    }

# ==================================================
# INIT
# ==================================================

seed = spawn_agent()
WORLD["agents"] = [seed]
reset_population(seed)
