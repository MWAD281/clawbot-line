from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 35 – Meta Strategy Brain")

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

POPULATION_SIZE = 16
INITIAL_CAPITAL = 100_000
EXTINCTION_LEVEL = 0.4
MUTATION_RATE = 0.3
PRESSURE_GROWTH = 1.15

STRATEGIES = ["TREND", "MEAN_REVERT", "VOLATILITY", "SURVIVAL"]
MARKETS = ["EQUITY", "CRYPTO", "COMMODITY"]

# ==================================================
# WORLD
# ==================================================

WORLD = {
    "epoch": 0,
    "generation": 1,
    "pressure": 1.0,
    "deception": 0.0,
    "agents": [],
    "champions": []
}

# ==================================================
# DNA
# ==================================================

def random_dna():
    return {
        "risk": round(random.uniform(0.01, 0.05), 3),
        "leverage": round(random.uniform(1.0, 4.0), 2),
        "adaptability": round(random.uniform(0.2, 1.0), 2),
        "memory_weight": round(random.uniform(0.3, 0.9), 2),
        "preferred_strategy": random.choice(STRATEGIES),
    }

def mutate_dna(dna):
    d = dna.copy()
    for k in d:
        if random.random() < MUTATION_RATE:
            if isinstance(d[k], float):
                d[k] = round(max(0.01, d[k] + random.uniform(-0.2, 0.2)), 3)
            elif isinstance(d[k], str):
                d[k] = random.choice(STRATEGIES)
    return d

# ==================================================
# AGENT
# ==================================================

def spawn_agent(dna=None, lineage=None, memory=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "capital": INITIAL_CAPITAL,
        "equity": INITIAL_CAPITAL,
        "peak": INITIAL_CAPITAL,
        "dna": dna or random_dna(),
        "strategy": None,
        "lineage": lineage or uuid.uuid4().hex[:6],
        "memory": memory or {
            "confidence": 0.5,
            "strategy_score": {s: 0.0 for s in STRATEGIES},
            "regime_error": 0.0
        },
        "age": 0
    }

def reset_population(champion):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        WORLD["agents"].append(
            spawn_agent(
                dna=mutate_dna(champion["dna"]),
                lineage=champion["lineage"],
                memory=copy.deepcopy(champion["memory"])
            )
        )

# ==================================================
# MARKET / REGIME
# ==================================================

def infer_regime(m):
    if m["volatility"] > 1.4:
        return "VOLATILE"
    if m["trend"] == "up":
        return "BULL"
    if m["trend"] == "down":
        return "BEAR"
    return "CHOP"

def deception(m):
    if random.random() < WORLD["deception"]:
        m = m.copy()
        m["trend"] = random.choice(["up", "down"])
        m["volatility"] *= random.uniform(0.4, 0.7)
    return m

# ==================================================
# META STRATEGY SELECTION
# ==================================================

def choose_strategy(agent, regime):
    scores = agent["memory"]["strategy_score"]

    if regime == "BULL":
        bias = "TREND"
    elif regime == "BEAR":
        bias = "SURVIVAL"
    elif regime == "VOLATILE":
        bias = "VOLATILITY"
    else:
        bias = "MEAN_REVERT"

    scores[bias] += agent["dna"]["adaptability"]

    return max(scores, key=scores.get)

# ==================================================
# SIMULATION
# ==================================================

def simulate(agent, market):
    if not agent["alive"]:
        return

    agent["age"] += 1
    regime = market["regime"]
    strategy = choose_strategy(agent, regime)
    agent["strategy"] = strategy

    edge = random.uniform(-1, 1)

    strategy_multiplier = {
        "TREND": 1.2 if regime == "BULL" else 0.8,
        "MEAN_REVERT": 1.1 if regime == "CHOP" else 0.7,
        "VOLATILITY": 1.3 if regime == "VOLATILE" else 0.6,
        "SURVIVAL": 0.6
    }[strategy]

    pnl = (
        agent["equity"]
        * agent["dna"]["risk"]
        * agent["dna"]["leverage"]
        * strategy_multiplier
        * market["volatility"]
        * WORLD["pressure"]
        * edge
    )

    agent["equity"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]
        agent["memory"]["strategy_score"][strategy] += 0.2
        agent["memory"]["confidence"] = min(1.0, agent["memory"]["confidence"] + 0.05)
    else:
        agent["memory"]["strategy_score"][strategy] -= 0.1
        agent["memory"]["confidence"] = max(0.0, agent["memory"]["confidence"] - 0.07)

    if agent["equity"] < INITIAL_CAPITAL * EXTINCTION_LEVEL:
        agent["alive"] = False

# ==================================================
# FITNESS & EVOLUTION
# ==================================================

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    return a["equity"] * (1 - dd) * (1 + a["age"] * 0.03)

def evolve():
    alive = [a for a in WORLD["agents"] if a["alive"]]

    if len(alive) <= 4:
        champion = max(WORLD["agents"], key=fitness)

        WORLD["champions"].append({
            "gen": WORLD["generation"],
            "id": champion["id"],
            "strategy": champion["strategy"],
            "equity": round(champion["equity"], 2)
        })

        WORLD["generation"] += 1
        WORLD["pressure"] *= PRESSURE_GROWTH
        WORLD["deception"] = min(0.65, WORLD["deception"] + 0.06)

        reset_population(champion)

# ==================================================
# API
# ==================================================

@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["epoch"] += 1

    market["regime"] = infer_regime(market)
    market = deception(market)

    for a in WORLD["agents"]:
        simulate(a, market)

    evolve()

    champ = max(WORLD["agents"], key=fitness)

    return {
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "regime": market["regime"],
        "pressure": round(WORLD["pressure"], 2),
        "deception": round(WORLD["deception"], 2),
        "champion": champ["id"],
        "agents": [
            {
                "id": a["id"],
                "eq": round(a["equity"], 2),
                "alive": a["alive"],
                "strategy": a["strategy"],
                "conf": round(a["memory"]["confidence"], 2)
            } for a in WORLD["agents"]
        ]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 35 ONLINE",
        "epoch": WORLD["epoch"],
        "generation": WORLD["generation"],
        "pressure": round(WORLD["pressure"], 2),
        "deception": round(WORLD["deception"], 2)
    }

# ==================================================
# INIT
# ==================================================

seed = spawn_agent()
WORLD["agents"] = [seed]
reset_population(seed)
