from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import random
import uuid

app = FastAPI(title="ClawBot Phase 26 – Capital War Civilization")

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
POPULATION_SIZE = 14
BASE_CAPITAL = 100_000
EXTINCTION_THRESHOLD = 0.4

BLACK_SWAN_PROB = 0.1
BLACK_SWAN_IMPACT = (-0.7, 0.7)

WORLDS = ["crypto", "equity", "macro"]
REGIMES = ["up", "down", "sideways"]

# -------------------------
# META-DNA (วิวัฒน์วิธีวิวัฒน์)
# -------------------------
def meta_gene():
    return {
        "mutation_rate": round(random.uniform(0.2, 0.6), 2),
        "risk_tolerance": round(random.uniform(0.5, 1.5), 2),
        "predation": round(random.uniform(0.1, 1.0), 2)  # ความดุ
    }

# -------------------------
# DNA
# -------------------------
def gene():
    return {
        "risk": round(random.uniform(0.01, 0.1), 3),
        "leverage": round(random.uniform(1.0, 7.0), 2),
        "aggression": round(random.uniform(0.3, 1.6), 2),
    }

def random_dna():
    return {
        "strategy": {w: {r: gene() for r in REGIMES} for w in WORLDS},
        "meta": meta_gene()
    }

def mutate_dna(dna):
    new = {"strategy": {}, "meta": dna["meta"].copy()}

    # meta evolution
    if random.random() < 0.4:
        new["meta"]["mutation_rate"] = round(
            max(0.1, min(0.8, new["meta"]["mutation_rate"] + random.uniform(-0.15, 0.15))), 2
        )
    if random.random() < 0.3:
        new["meta"]["predation"] = round(
            max(0.0, min(1.5, new["meta"]["predation"] + random.uniform(-0.3, 0.3))), 2
        )

    # strategy genes
    for w in dna["strategy"]:
        new["strategy"][w] = {}
        for r in dna["strategy"][w]:
            g = dna["strategy"][w][r].copy()
            if random.random() < new["meta"]["mutation_rate"]:
                g["risk"] = round(max(0.005, min(0.2, g["risk"] + random.uniform(-0.04, 0.04))), 3)
            if random.random() < new["meta"]["mutation_rate"]:
                g["leverage"] = round(max(1.0, min(10.0, g["leverage"] + random.uniform(-2, 2))), 2)
            if random.random() < new["meta"]["mutation_rate"]:
                g["aggression"] = round(max(0.1, min(2.0, g["aggression"] + random.uniform(-0.5, 0.5))), 2)
            new["strategy"][w][r] = g

    return new

# -------------------------
# WORLD STATE
# -------------------------
WORLD = {
    "step": 0,
    "generation": 1,
    "funds": {},
    "agents": []
}

# -------------------------
# AGENT / FUND
# -------------------------
def spawn_agent(dna=None, fund=None, capital=BASE_CAPITAL):
    if fund is None:
        fund = uuid.uuid4().hex[:4]
        WORLD["funds"][fund] = {"aum": 0, "agents": 0, "kills": 0}

    WORLD["funds"][fund]["aum"] += capital
    WORLD["funds"][fund]["agents"] += 1

    return {
        "id": uuid.uuid4().hex[:8],
        "fund": fund,
        "alive": True,
        "equity": capital,
        "peak": capital,
        "dna": dna or random_dna(),
        "score": 0.0
    }

# -------------------------
# FITNESS
# -------------------------
def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    return a["equity"] * (1 - dd)

# -------------------------
# SIMULATION
# -------------------------
def simulate_agent(agent, market, black_swan=False):
    if not agent["alive"]:
        return

    w = market.get("world", "crypto")
    r = market.get("trend", "sideways")
    g = agent["dna"]["strategy"][w][r]
    meta = agent["dna"]["meta"]

    edge = random.uniform(-1, 1)
    shock = random.uniform(*BLACK_SWAN_IMPACT) if black_swan else 0

    conviction = g["risk"] * g["leverage"] * g["aggression"] * meta["risk_tolerance"]
    pnl = agent["equity"] * conviction * (edge + shock) * 0.01

    agent["equity"] += pnl
    agent["score"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_THRESHOLD:
        agent["alive"] = False
        WORLD["funds"][agent["fund"]]["agents"] -= 1

# -------------------------
# HOSTILE TAKEOVER
# -------------------------
def predation_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) < 2:
        return

    hunter = random.choice(alive)
    prey = random.choice([a for a in alive if a["fund"] != hunter["fund"]])

    aggression = hunter["dna"]["meta"]["predation"]
    if random.random() < aggression:
        steal = prey["equity"] * random.uniform(0.05, 0.25)
        prey["equity"] -= steal
        hunter["equity"] += steal
        WORLD["funds"][hunter["fund"]]["aum"] += steal
        WORLD["funds"][prey["fund"]]["aum"] -= steal
        WORLD["funds"][hunter["fund"]]["kills"] += 1

# -------------------------
# EVOLUTION
# -------------------------
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) <= 5:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["generation"] += 1
        WORLD["agents"] = []
        for _ in range(POPULATION_SIZE):
            WORLD["agents"].append(
                spawn_agent(
                    dna=mutate_dna(champion["dna"]),
                    fund=champion["fund"]
                )
            )

# -------------------------
# API
# -------------------------
@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["step"] += 1
    black_swan = random.random() < BLACK_SWAN_PROB

    for agent in WORLD["agents"]:
        simulate_agent(agent, market, black_swan)

    predation_step()
    evolution_step()

    champion = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "black_swan": black_swan,
        "champion": champion["id"],
        "funds": WORLD["funds"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 26 running",
        "generation": WORLD["generation"],
        "funds": len(WORLD["funds"])
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "funds": WORLD["funds"],
        "agents": sorted(WORLD["agents"], key=fitness, reverse=True)
    }

# -------------------------
# INIT
# -------------------------
WORLD["agents"] = [spawn_agent() for _ in range(POPULATION_SIZE)]
