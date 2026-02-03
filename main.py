from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 33 – Multi-Market Extinction")

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

POPULATION_SIZE = 12
INITIAL_CASH = 100_000
EXTINCTION_LEVEL = 0.45
MUTATION_RATE = 0.30
PRESSURE_GROWTH = 1.15

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
    "extinction_events": []
}

# ==================================================
# DNA
# ==================================================

def random_dna():
    return {
        "risk": round(random.uniform(0.01, 0.07), 3),
        "leverage": round(random.uniform(1.0, 4.5), 2),
        "aggression": round(random.uniform(0.2, 1.0), 2),
        "discipline": round(random.uniform(0.3, 0.95), 2),
        "market_bias": random.choice(MARKETS),
        "regime_bias": random.choice(["RISK_ON", "RISK_OFF", "VOLATILE"])
    }

def mutate_dna(dna):
    d = dna.copy()
    for k in d:
        if random.random() < MUTATION_RATE:
            if isinstance(d[k], float):
                d[k] = round(max(0.01, d[k] + random.uniform(-0.15, 0.15)), 3)
            elif isinstance(d[k], str):
                if k == "market_bias":
                    d[k] = random.choice(MARKETS)
                else:
                    d[k] = random.choice(["RISK_ON", "RISK_OFF", "VOLATILE"])
    return d

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
        "memory": {
            "confidence": 0.5,
            "trauma": 0.0
        },
        "lineage": lineage or uuid.uuid4().hex[:6],
        "last_pnl": 0.0
    }

def reset_population(champion):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        WORLD["agents"].append(
            spawn_agent(
                dna=mutate_dna(champion["dna"]),
                lineage=champion["lineage"]
            )
        )

# ==================================================
# REGIME / MARKET
# ==================================================

def infer_regime(market):
    if market["volatility"] > 1.6:
        return "VOLATILE"
    if market["trend"] == "up":
        return "RISK_ON"
    if market["trend"] == "down":
        return "RISK_OFF"
    return "NEUTRAL"

def market_multiplier(market_type):
    return {
        "EQUITY": 1.0,
        "CRYPTO": 1.6,
        "COMMODITY": 0.8
    }[market_type]

# ==================================================
# FITNESS
# ==================================================

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    return a["equity"] * (1 - dd) * a["memory"]["confidence"]

# ==================================================
# SIMULATION
# ==================================================

def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    dna = agent["dna"]
    mem = agent["memory"]

    regime_match = 1.2 if dna["regime_bias"] == market["regime"] else 0.75
    market_match = 1.3 if dna["market_bias"] == WORLD["active_market"] else 0.7

    edge = random.uniform(-1, 1)

    pnl = (
        agent["equity"]
        * dna["risk"]
        * dna["leverage"]
        * dna["aggression"]
        * regime_match
        * market_match
        * market["volatility"]
        * WORLD["pressure"]
        * edge
    )

    pnl *= (1 - dna["discipline"] * mem["trauma"])

    agent["equity"] += pnl
    agent["last_pnl"] = pnl

    if pnl > 0:
        mem["confidence"] = min(1.0, mem["confidence"] + 0.05)
    else:
        mem["trauma"] = min(1.0, mem["trauma"] + 0.12)
        mem["confidence"] = max(0.0, mem["confidence"] - 0.07)

    mem["trauma"] *= 0.9

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < INITIAL_CASH * EXTINCTION_LEVEL:
        agent["alive"] = False

# ==================================================
# EVOLUTION + EXTINCTION CASCADE
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
        WORLD["pressure"] *= PRESSURE_GROWTH

        WORLD["extinction_events"].append({
            "gen": WORLD["generation"],
            "market": WORLD["active_market"],
            "pressure": round(WORLD["pressure"], 2)
        })

        reset_population(champion)

# ==================================================
# API
# ==================================================

@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["epoch"] += 1

    WORLD["active_market"] = market.get("market", random.choice(MARKETS))
    market["regime"] = infer_regime(market)

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
        "champion": champion["id"],
        "agents": [
            {
                "id": a["id"],
                "eq": round(a["equity"], 2),
                "alive": a["alive"],
                "conf": round(a["memory"]["confidence"], 2),
                "market_bias": a["dna"]["market_bias"],
                "lineage": a["lineage"]
            } for a in WORLD["agents"]
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 33 ONLINE",
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "pressure": round(WORLD["pressure"], 2),
        "extinctions": len(WORLD["extinction_events"]),
        "lineages": len(WORLD["lineages"])
    }

@app.get("/lineages")
def lineages():
    return WORLD["lineages"][-10:]

@app.get("/extinctions")
def extinctions():
    return WORLD["extinction_events"][-10:]

# ==================================================
# INIT
# ==================================================

seed = spawn_agent()
WORLD["agents"] = [seed]
reset_population(seed)
