from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid

app = FastAPI(title="ClawBot Phase 23 – MultiWorld Council Darwinism")

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
POPULATION_SIZE = 9
INITIAL_EQUITY = 100_000
KILL_THRESHOLD = 0.55
MUTATION_RATE = 0.3

REGIMES = ["up", "down", "sideways"]
WORLDS = ["crypto", "equity", "macro"]

# -------------------------
# DNA
# -------------------------
def random_gene():
    return {
        "risk": round(random.uniform(0.01, 0.06), 3),
        "leverage": round(random.uniform(1.0, 4.0), 2),
        "aggression": round(random.uniform(0.2, 1.0), 2),
    }

def random_dna():
    return {
        world: {
            regime: random_gene()
            for regime in REGIMES
        }
        for world in WORLDS
    }

def mutate_dna(dna):
    new = {}
    for world, regimes in dna.items():
        new[world] = {}
        for regime, gene in regimes.items():
            g = gene.copy()
            if random.random() < MUTATION_RATE:
                g["risk"] = round(max(0.005, min(0.1, g["risk"] + random.uniform(-0.02, 0.02))), 3)
            if random.random() < MUTATION_RATE:
                g["leverage"] = round(max(1.0, min(6.0, g["leverage"] + random.uniform(-0.8, 0.8))), 2)
            if random.random() < MUTATION_RATE:
                g["aggression"] = round(max(0.1, min(1.2, g["aggression"] + random.uniform(-0.2, 0.2))), 2)
            new[world][regime] = g
    return new

# -------------------------
# WORLD STATE
# -------------------------
WORLD = {
    "step": 0,
    "generation": 1,
    "agents": []
}

def spawn_agent(dna=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "generation": WORLD["generation"],
        "alive": True,
        "equity": INITIAL_EQUITY,
        "peak": INITIAL_EQUITY,
        "last_return": 0.0,
        "dna": dna or random_dna(),
        "score": {w: 0.0 for w in WORLDS}
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
    multi_world_score = sum(agent["score"].values())
    return agent["equity"] * (1 - dd) + multi_world_score * 15

# -------------------------
# REGIME + COUNCIL
# -------------------------
def detect_regime(market):
    return market.get("trend", "sideways")

def council_vote(agent, world, regime):
    gene = agent["dna"][world][regime]
    conviction = (
        gene["risk"]
        * gene["leverage"]
        * gene["aggression"]
        * random.uniform(0.7, 1.3)
    )
    return conviction

# -------------------------
# SIMULATION
# -------------------------
def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    world = market.get("world", "crypto")
    regime = detect_regime(market)

    vote = council_vote(agent, world, regime)
    edge = random.uniform(-1, 1)

    pnl = agent["equity"] * vote * edge * 0.01
    agent["equity"] += pnl
    agent["last_return"] = pnl / max(agent["equity"], 1)

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    agent["score"][world] += agent["last_return"]

    if agent["equity"] < INITIAL_EQUITY * KILL_THRESHOLD:
        agent["alive"] = False

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

    evolution_step()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "world": market.get("world"),
        "regime": market.get("trend"),
        "champion": champion["id"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 23 running",
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
