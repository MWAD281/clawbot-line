from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import random
import uuid

app = FastAPI(title="ClawBot Phase 25 – Civilization Darwinism")

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
POPULATION_SIZE = 12
BASE_CAPITAL = 100_000
EXTINCTION_THRESHOLD = 0.45
MUTATION_RATE = 0.4
MEMORY_DECAY = 0.9

BLACK_SWAN_PROB = 0.08
BLACK_SWAN_IMPACT = (-0.6, 0.6)

WORLDS = ["crypto", "equity", "macro"]
REGIMES = ["up", "down", "sideways"]

# -------------------------
# DNA
# -------------------------
def gene():
    return {
        "risk": round(random.uniform(0.01, 0.09), 3),
        "leverage": round(random.uniform(1.0, 6.0), 2),
        "aggression": round(random.uniform(0.2, 1.4), 2),
    }

def random_dna():
    return {w: {r: gene() for r in REGIMES} for w in WORLDS}

def mutate_dna(dna):
    new = {}
    for w in dna:
        new[w] = {}
        for r in dna[w]:
            g = dna[w][r].copy()
            if random.random() < MUTATION_RATE:
                g["risk"] = round(max(0.005, min(0.15, g["risk"] + random.uniform(-0.03, 0.03))), 3)
            if random.random() < MUTATION_RATE:
                g["leverage"] = round(max(1.0, min(8.0, g["leverage"] + random.uniform(-1.2, 1.2))), 2)
            if random.random() < MUTATION_RATE:
                g["aggression"] = round(max(0.1, min(1.7, g["aggression"] + random.uniform(-0.4, 0.4))), 2)
            new[w][r] = g
    return new

# -------------------------
# WORLD STATE
# -------------------------
WORLD = {
    "step": 0,
    "generation": 1,
    "species_counter": 0,
    "dynasties": {},
    "agents": []
}

# -------------------------
# AGENT / SPECIES
# -------------------------
def spawn_agent(dna=None, species_id=None, capital=BASE_CAPITAL):
    if species_id is None:
        WORLD["species_counter"] += 1
        species_id = f"S{WORLD['species_counter']}"

    if species_id not in WORLD["dynasties"]:
        WORLD["dynasties"][species_id] = {
            "born": WORLD["generation"],
            "champions": 0,
            "alive": 0
        }

    WORLD["dynasties"][species_id]["alive"] += 1

    return {
        "id": uuid.uuid4().hex[:8],
        "species": species_id,
        "generation": WORLD["generation"],
        "alive": True,
        "equity": capital,
        "peak": capital,
        "dna": dna or random_dna(),
        "memory": {w: {r: 0.0 for r in REGIMES} for w in WORLDS},
        "score": 0.0
    }

def reset_population(seed):
    WORLD["agents"] = []
    for _ in range(POPULATION_SIZE):
        if random.random() < 0.3:
            WORLD["agents"].append(
                spawn_agent(
                    dna=mutate_dna(seed["dna"]),
                    species_id=None
                )
            )
        else:
            WORLD["agents"].append(
                spawn_agent(
                    dna=mutate_dna(seed["dna"]),
                    species_id=seed["species"]
                )
            )

# -------------------------
# FITNESS
# -------------------------
def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    trauma = sum(abs(v) for w in a["memory"].values() for v in w.values())
    return a["equity"] * (1 - dd) - trauma * 600

# -------------------------
# REGIME
# -------------------------
def regime(market):
    return market.get("trend", "sideways")

# -------------------------
# SIMULATION
# -------------------------
def simulate_agent(agent, market, black_swan=False):
    if not agent["alive"]:
        return

    w = market.get("world", "crypto")
    r = regime(market)
    g = agent["dna"][w][r]

    fear = agent["memory"][w][r]
    conviction = g["risk"] * g["leverage"] * g["aggression"] * (1 - min(fear, 0.9))

    edge = random.uniform(-1, 1)
    shock = random.uniform(*BLACK_SWAN_IMPACT) if black_swan else 0

    pnl = agent["equity"] * conviction * (edge + shock) * 0.01
    agent["equity"] += pnl

    if pnl < 0:
        agent["memory"][w][r] += abs(pnl) / max(agent["equity"], 1)
    else:
        agent["memory"][w][r] *= MEMORY_DECAY

    agent["score"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_THRESHOLD:
        agent["alive"] = False
        WORLD["dynasties"][agent["species"]]["alive"] -= 1

# -------------------------
# EVOLUTION
# -------------------------
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) <= 4:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["dynasties"][champion["species"]]["champions"] += 1
        WORLD["generation"] += 1
        reset_population(champion)

# -------------------------
# API
# -------------------------
@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["step"] += 1

    black_swan = random.random() < BLACK_SWAN_PROB

    for agent in WORLD["agents"]:
        simulate_agent(agent, market, black_swan)

    evolution_step()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "black_swan": black_swan,
        "champion": champion["id"],
        "species": champion["species"],
        "dynasties": WORLD["dynasties"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 25 running",
        "generation": WORLD["generation"],
        "species": len(WORLD["dynasties"])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "dynasties": WORLD["dynasties"],
        "agents": sorted(WORLD["agents"], key=fitness, reverse=True)
    }

# -------------------------
# INIT
# -------------------------
WORLD["agents"] = [spawn_agent() for _ in range(POPULATION_SIZE)]
