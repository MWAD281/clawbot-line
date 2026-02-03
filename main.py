from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import random
import uuid

app = FastAPI(title="ClawBot Phase 22 – Regime-Aware Darwinism")

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# CONFIG
# -------------------------
POPULATION_SIZE = 6
INITIAL_CASH = 100_000
KILL_THRESHOLD = 0.6
MUTATION_RATE = 0.25

REGIMES = ["up", "down", "sideways"]

# -------------------------
# DNA
# -------------------------
def random_dna():
    return {
        regime: {
            "risk": round(random.uniform(0.01, 0.05), 3),
            "leverage": round(random.uniform(1.0, 3.0), 2),
            "aggression": round(random.uniform(0.2, 0.9), 2),
        }
        for regime in REGIMES
    }

def mutate_dna(dna):
    new = {}
    for regime, genes in dna.items():
        g = genes.copy()
        if random.random() < MUTATION_RATE:
            g["risk"] = round(max(0.005, min(0.08, g["risk"] + random.uniform(-0.01, 0.01))), 3)
        if random.random() < MUTATION_RATE:
            g["leverage"] = round(max(1.0, min(5.0, g["leverage"] + random.uniform(-0.5, 0.5))), 2)
        if random.random() < MUTATION_RATE:
            g["aggression"] = round(max(0.1, min(1.0, g["aggression"] + random.uniform(-0.1, 0.1))), 2)
        new[regime] = g
    return new

# -------------------------
# WORLD
# -------------------------
WORLD = {
    "step": 0,
    "generation": 1,
    "market": {},
    "agents": []
}

def spawn_agent(dna=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": INITIAL_CASH,
        "peak": INITIAL_CASH,
        "last_return": 0.0,
        "dna": dna or random_dna(),
        "regime_score": {r: 0.0 for r in REGIMES}
    }

def reset_population(seed_dna=None):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        if seed_dna:
            WORLD["agents"].append(spawn_agent(mutate_dna(seed_dna)))
        else:
            WORLD["agents"].append(spawn_agent())

# -------------------------
# FITNESS
# -------------------------
def fitness(agent):
    dd = (agent["peak"] - agent["equity"]) / agent["peak"]
    regime_bonus = sum(agent["regime_score"].values())
    return agent["equity"] * (1 - dd) + regime_bonus * 10

# -------------------------
# SIMULATION
# -------------------------
def detect_regime(market):
    trend = market.get("trend", "sideways")
    if trend == "up":
        return "up"
    if trend == "down":
        return "down"
    return "sideways"

def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    regime = detect_regime(market)
    gene = agent["dna"][regime]

    vol = market.get("volatility", "normal")
    vol_factor = {"normal": 0.5, "high": 1.0, "extreme": 2.0}.get(vol, 1.0)

    edge = random.uniform(-1, 1)
    pnl = (
        agent["equity"]
        * gene["risk"]
        * gene["leverage"]
        * gene["aggression"]
        * vol_factor
        * edge
    )

    agent["equity"] += pnl
    agent["last_return"] = pnl / max(agent["equity"], 1)

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    agent["regime_score"][regime] += agent["last_return"]

    if agent["equity"] < INITIAL_CASH * KILL_THRESHOLD:
        agent["alive"] = False

# -------------------------
# EVOLUTION
# -------------------------
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) <= 2:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["generation"] += 1
        reset_population(seed_dna=champion["dna"])

# -------------------------
# API
# -------------------------
@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["step"] += 1
    WORLD["market"] = market

    for agent in WORLD["agents"]:
        simulate_agent(agent, market)

    evolution_step()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "regime": detect_regime(market),
        "champion": champion["id"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 22 running",
        "generation": WORLD["generation"],
        "step": WORLD["step"]
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "agents": sorted(WORLD["agents"], key=fitness, reverse=True)
    }

# -------------------------
# INIT
# -------------------------
reset_population()
