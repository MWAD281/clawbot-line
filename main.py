from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import random
import uuid

app = FastAPI(title="ClawBot Phase 27 – Self Governing Market Civilization")

# =====================
# CORS
# =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# CONFIG
# =====================
POPULATION = 16
BASE_CAPITAL = 100_000
EXTINCTION_LEVEL = 0.35

WORLD_TYPES = ["crypto", "equity", "macro"]
TRENDS = ["up", "down", "side"]

# =====================
# DNA
# =====================
def strategy_gene():
    return {
        "risk": round(random.uniform(0.01, 0.15), 3),
        "leverage": round(random.uniform(1, 10), 2),
        "aggression": round(random.uniform(0.3, 2.0), 2),
    }

def meta_gene():
    return {
        "mutation_rate": round(random.uniform(0.2, 0.7), 2),
        "predation": round(random.uniform(0.0, 1.5), 2),
        "rule_breaker": round(random.uniform(0.0, 1.0), 2),
    }

def random_dna():
    return {
        "strategy": {
            w: {t: strategy_gene() for t in TRENDS}
            for w in WORLD_TYPES
        },
        "meta": meta_gene()
    }

def mutate_dna(dna):
    new = {"strategy": {}, "meta": dna["meta"].copy()}
    m = new["meta"]

    if random.random() < 0.4:
        m["mutation_rate"] = round(max(0.1, min(0.9, m["mutation_rate"] + random.uniform(-0.2, 0.2))), 2)
    if random.random() < 0.3:
        m["predation"] = round(max(0.0, min(2.0, m["predation"] + random.uniform(-0.4, 0.4))), 2)
    if random.random() < 0.3:
        m["rule_breaker"] = round(max(0.0, min(1.5, m["rule_breaker"] + random.uniform(-0.3, 0.3))), 2)

    for w in dna["strategy"]:
        new["strategy"][w] = {}
        for t in dna["strategy"][w]:
            g = dna["strategy"][w][t].copy()
            if random.random() < m["mutation_rate"]:
                g["risk"] = round(max(0.005, min(0.25, g["risk"] + random.uniform(-0.05, 0.05))), 3)
            if random.random() < m["mutation_rate"]:
                g["leverage"] = round(max(1.0, min(15.0, g["leverage"] + random.uniform(-3, 3))), 2)
            if random.random() < m["mutation_rate"]:
                g["aggression"] = round(max(0.1, min(3.0, g["aggression"] + random.uniform(-0.6, 0.6))), 2)
            new["strategy"][w][t] = g

    return new

# =====================
# WORLD STATE
# =====================
WORLD = {
    "step": 0,
    "generation": 1,
    "law": {
        "tax": 0.02,
        "reward_mode": "equity"
    },
    "agents": []
}

# =====================
# AGENT
# =====================
def spawn_agent(dna=None, capital=BASE_CAPITAL):
    return {
        "id": uuid.uuid4().hex[:8],
        "alive": True,
        "equity": capital,
        "peak": capital,
        "dna": dna or random_dna(),
        "score": 0.0,
    }

# =====================
# FITNESS
# =====================
def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    if WORLD["law"]["reward_mode"] == "equity":
        return a["equity"] * (1 - dd)
    if WORLD["law"]["reward_mode"] == "survival":
        return a["equity"] * (1 - dd * 2)
    return a["equity"]

# =====================
# MARKET SIM
# =====================
def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    w = market["world"]
    t = market["trend"]
    g = agent["dna"]["strategy"][w][t]
    meta = agent["dna"]["meta"]

    edge = random.uniform(-1, 1)
    chaos = random.uniform(-1, 1) * meta["rule_breaker"]

    conviction = g["risk"] * g["leverage"] * g["aggression"]
    pnl = agent["equity"] * conviction * (edge + chaos) * 0.01

    tax = abs(pnl) * WORLD["law"]["tax"]
    agent["equity"] += pnl - tax
    agent["score"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_LEVEL:
        agent["alive"] = False

# =====================
# CIVIL WAR / PREDATION
# =====================
def civil_war():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) < 2:
        return

    hunter = random.choice(alive)
    prey = random.choice([a for a in alive if a["id"] != hunter["id"]])

    if random.random() < hunter["dna"]["meta"]["predation"]:
        steal = prey["equity"] * random.uniform(0.05, 0.3)
        prey["equity"] -= steal
        hunter["equity"] += steal

# =====================
# LAW EVOLUTION
# =====================
def evolve_law():
    if random.random() < 0.15:
        WORLD["law"]["tax"] = round(random.uniform(0.0, 0.05), 3)

    if random.random() < 0.1:
        WORLD["law"]["reward_mode"] = random.choice(["equity", "survival"])

# =====================
# REBOOT CIVILIZATION
# =====================
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]

    if len(alive) <= 4:
        champion = max(WORLD["agents"], key=fitness)
        WORLD["generation"] += 1
        WORLD["agents"] = [
            spawn_agent(dna=mutate_dna(champion["dna"]))
            for _ in range(POPULATION)
        ]

# =====================
# API
# =====================
@app.post("/simulate/market")
def simulate_market(market: Dict):
    WORLD["step"] += 1

    for a in WORLD["agents"]:
        simulate_agent(a, market)

    civil_war()
    evolve_law()
    evolution_step()

    champ = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "law": WORLD["law"],
        "champion": champ["id"],
        "agents": WORLD["agents"]
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 27 online",
        "generation": WORLD["generation"],
        "law": WORLD["law"]
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "law": WORLD["law"],
        "agents": sorted(WORLD["agents"], key=fitness, reverse=True)
    }

# =====================
# INIT
# =====================
WORLD["agents"] = [spawn_agent() for _ in range(POPULATION)]
