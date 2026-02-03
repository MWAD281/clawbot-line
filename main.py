from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import random
import uuid
import time

app = FastAPI(title="ClawBot Phase 21 – Hardcore Darwinism")

# -------------------------
# CORS (จำเป็นบน Render)
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
KILL_THRESHOLD = 0.6  # equity < 60% = ตาย
MUTATION_RATE = 0.25

# -------------------------
# DNA / AGENT
# -------------------------
def random_dna():
    return {
        "risk_per_trade": round(random.uniform(0.01, 0.05), 3),
        "leverage": round(random.uniform(1.0, 3.0), 2),
        "aggression": round(random.uniform(0.2, 0.9), 2),
        "volatility_bias": random.choice(["low", "mid", "high"])
    }

def mutate_dna(dna):
    new = dna.copy()
    if random.random() < MUTATION_RATE:
        new["risk_per_trade"] = round(
            max(0.005, min(0.08, dna["risk_per_trade"] + random.uniform(-0.01, 0.01))), 3
        )
    if random.random() < MUTATION_RATE:
        new["leverage"] = round(
            max(1.0, min(5.0, dna["leverage"] + random.uniform(-0.5, 0.5))), 2
        )
    if random.random() < MUTATION_RATE:
        new["aggression"] = round(
            max(0.1, min(1.0, dna["aggression"] + random.uniform(-0.1, 0.1))), 2
        )
    return new

# -------------------------
# WORLD STATE
# -------------------------
WORLD: Dict = {
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
        "cash": INITIAL_CASH,
        "equity": INITIAL_CASH,
        "peak": INITIAL_CASH,
        "last_return": 0.0,
        "dna": dna or random_dna()
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
    return agent["equity"] * (1 - dd)

# -------------------------
# SIMULATION CORE
# -------------------------
def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    dna = agent["dna"]

    volatility_factor = {
        "low": 0.5,
        "mid": 1.0,
        "high": 1.5
    }[dna["volatility_bias"]]

    market_vol = {
        "normal": 0.5,
        "high": 1.0,
        "extreme": 2.0
    }.get(market["volatility"], 1.0)

    edge = random.uniform(-1, 1)
    pnl = (
        agent["equity"]
        * dna["risk_per_trade"]
        * dna["leverage"]
        * dna["aggression"]
        * volatility_factor
        * market_vol
        * edge
    )

    agent["equity"] += pnl
    agent["last_return"] = pnl / max(agent["equity"], 1)

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < INITIAL_CASH * KILL_THRESHOLD:
        agent["alive"] = False

# -------------------------
# EVOLUTION STEP
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
        "market": market,
        "champion": champion["id"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 21 running",
        "step": WORLD["step"],
        "generation": WORLD["generation"]
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "step": WORLD["step"],
        "agents": sorted(
            WORLD["agents"],
            key=lambda a: a["equity"],
            reverse=True
        )
    }

# -------------------------
# INIT
# -------------------------
reset_population()
