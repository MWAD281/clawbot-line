from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import random
import uuid

app = FastAPI(title="ClawBot Phase 24 – True Darwinism")

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
POPULATION_SIZE = 10
BASE_CAPITAL = 100_000
EXTINCTION_THRESHOLD = 0.5
MUTATION_RATE = 0.35
MEMORY_DECAY = 0.92

WORLDS = ["crypto", "equity", "macro"]
REGIMES = ["up", "down", "sideways"]

# -------------------------
# DNA
# -------------------------
def gene():
    return {
        "risk": round(random.uniform(0.01, 0.07), 3),
        "leverage": round(random.uniform(1.0, 5.0), 2),
        "aggression": round(random.uniform(0.2, 1.2), 2),
    }

def random_dna():
    return {
        w: {r: gene() for r in REGIMES}
        for w in WORLDS
    }

def mutate_dna(dna):
    new = {}
    for w, regimes in dna.items():
        new[w] = {}
        for r, g in regimes.items():
            m = g.copy()
            if random.random() < MUTATION_RATE:
                m["risk"] = round(max(0.005, min(0.12, m["risk"] + random.uniform(-0.02, 0.02))), 3)
            if random.random() < MUTATION_RATE:
                m["leverage"] = round(max(1.0, min(7.0, m["leverage"] + random.uniform(-1, 1))), 2)
            if random.random() < MUTATION_RATE:
                m["aggression"] = round(max(0.1, min(1.5, m["aggression"] + random.uniform(-0.3, 0.3))), 2)
            new[w][r] = m
    return new

# -------------------------
# WORLD STATE
# -------------------------
WORLD = {
    "step": 0,
    "generation": 1,
    "agents": [],
    "extinct_dna": 0
}

# -------------------------
# AGENT
# -------------------------
def spawn_agent(dna=None, capital=BASE_CAPITAL):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": capital,
        "peak": capital,
        "last_return": 0.0,
        "dna": dna or random_dna(),
        "memory": {w: {r: 0.0 for r in REGIMES} for w in WORLDS},
        "allocation": capital,
        "score": 0.0
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
def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    memory_penalty = sum(abs(v) for w in a["memory"].values() for v in w.values())
    return a["equity"] * (1 - dd) - memory_penalty * 500

# -------------------------
# REGIME
# -------------------------
def regime(market):
    return market.get("trend", "sideways")

# -------------------------
# SIMULATION
# -------------------------
def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    w = market.get("world", "crypto")
    r = regime(market)
    gene = agent["dna"][w][r]

    fear = agent["memory"][w][r]
    conviction = (
        gene["risk"]
        * gene["leverage"]
        * gene["aggression"]
        * (1 - min(fear, 0.8))
    )

    edge = random.uniform(-1, 1)
    pnl = agent["equity"] * conviction * edge * 0.012

    agent["equity"] += pnl
    agent["last_return"] = pnl / max(agent["equity"], 1)

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    # Memory (trauma)
    if pnl < 0:
        agent["memory"][w][r] += abs(agent["last_return"])
    else:
        agent["memory"][w][r] *= MEMORY_DECAY

    agent["score"] += agent["last_return"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_THRESHOLD:
        agent["alive"] = False
        WORLD["extinct_dna"] += 1

# -------------------------
# CAPITAL ALLOCATOR
# -------------------------
def allocate_capital():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if not alive:
        return

    total_fitness = sum(max(fitness(a), 1) for a in alive)
    pool = BASE_CAPITAL * len(alive)

    for a in alive:
        share = max(fitness(a), 1) / total_fitness
        a["allocation"] = pool * share
        a["equity"] = a["allocation"]
        a["peak"] = a["allocation"]

# -------------------------
# EVOLUTION
# -------------------------
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) <= 3:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["generation"] += 1
        reset_population(seed_dna=champion["dna"])

# -------------------------
# API
# -------------------------
@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["step"] += 1

    for agent in WORLD["agents"]:
        simulate_agent(agent, market)

    allocate_capital()
    evolution_step()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "world": market.get("world"),
        "regime": market.get("trend"),
        "champion": champion["id"],
        "extinct_dna": WORLD["extinct_dna"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 24 running",
        "generation": WORLD["generation"],
        "step": WORLD["step"],
        "extinct_dna": WORLD["extinct_dna"]
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
