from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid

app = FastAPI(title="ClawBot Phase 28 – Autonomous Goal-Driven Civilization")

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
POPULATION = 20
BASE_CAPITAL = 100_000
EXTINCTION_LEVEL = 0.4
GOALS = ["GROWTH", "SURVIVAL", "DOMINANCE"]
WORLD_TYPES = ["crypto", "equity", "macro"]
TRENDS = ["up", "down", "side"]

# =====================
# DNA
# =====================
def strategy_gene():
    return {
        "risk": round(random.uniform(0.01, 0.2), 3),
        "leverage": round(random.uniform(1, 12), 2),
        "aggression": round(random.uniform(0.2, 2.5), 2),
    }

def meta_gene():
    return {
        "mutation_rate": round(random.uniform(0.2, 0.8), 2),
        "rule_breaker": round(random.uniform(0.0, 1.5), 2),
        "adaptivity": round(random.uniform(0.2, 1.5), 2),
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
    m = dna["meta"]
    new = {"strategy": {}, "meta": m.copy()}

    if random.random() < 0.5:
        new["meta"]["mutation_rate"] = round(
            max(0.1, min(0.9, m["mutation_rate"] + random.uniform(-0.2, 0.2))), 2
        )
    if random.random() < 0.4:
        new["meta"]["rule_breaker"] = round(
            max(0.0, min(2.0, m["rule_breaker"] + random.uniform(-0.4, 0.4))), 2
        )
    if random.random() < 0.4:
        new["meta"]["adaptivity"] = round(
            max(0.1, min(2.0, m["adaptivity"] + random.uniform(-0.3, 0.3))), 2
        )

    for w in dna["strategy"]:
        new["strategy"][w] = {}
        for t in dna["strategy"][w]:
            g = dna["strategy"][w][t].copy()
            if random.random() < new["meta"]["mutation_rate"]:
                g["risk"] = round(max(0.005, min(0.3, g["risk"] + random.uniform(-0.05, 0.05))), 3)
            if random.random() < new["meta"]["mutation_rate"]:
                g["leverage"] = round(max(1.0, min(20.0, g["leverage"] + random.uniform(-4, 4))), 2)
            if random.random() < new["meta"]["mutation_rate"]:
                g["aggression"] = round(max(0.1, min(3.5, g["aggression"] + random.uniform(-0.7, 0.7))), 2)
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
        "reward_mode": "equity",  # equity | survival | dominance
    },
    "culture": {
        "dominant_goal": "GROWTH"
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
        "goal": random.choice(GOALS),
        "age": 0,
        "score": 0.0,
    }

# =====================
# FITNESS (Goal-driven)
# =====================
def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    if a["goal"] == "GROWTH":
        return a["equity"] * (1 - dd)
    if a["goal"] == "SURVIVAL":
        return a["equity"] * (1 - dd * 2)
    if a["goal"] == "DOMINANCE":
        return a["score"]
    return a["equity"]

# =====================
# GOAL ADAPTATION
# =====================
def adapt_goal(agent):
    if agent["equity"] < BASE_CAPITAL * 0.7:
        agent["goal"] = "SURVIVAL"
    elif agent["score"] > BASE_CAPITAL * 0.5:
        agent["goal"] = "DOMINANCE"
    elif agent["equity"] > agent["peak"] * 1.2:
        agent["goal"] = "GROWTH"

# =====================
# MARKET SIM
# =====================
def simulate_agent(agent, market):
    if not agent["alive"]:
        return

    agent["age"] += 1
    w, t = market["world"], market["trend"]
    g = agent["dna"]["strategy"][w][t]
    meta = agent["dna"]["meta"]

    edge = random.uniform(-1, 1)
    chaos = random.uniform(-1, 1) * meta["rule_breaker"]
    intent = 1.0 if agent["goal"] == "GROWTH" else (0.7 if agent["goal"] == "SURVIVAL" else 1.3)

    conviction = g["risk"] * g["leverage"] * g["aggression"] * intent
    pnl = agent["equity"] * conviction * (edge + chaos) * 0.01

    tax = abs(pnl) * WORLD["law"]["tax"]
    agent["equity"] += pnl - tax
    agent["score"] += pnl

    if agent["equity"] > agent["peak"]:
        agent["peak"] = agent["equity"]

    if agent["equity"] < BASE_CAPITAL * EXTINCTION_LEVEL:
        agent["alive"] = False

    adapt_goal(agent)

# =====================
# CULTURE & LAW EVOLUTION
# =====================
def evolve_culture_and_law():
    goals = [a["goal"] for a in WORLD["agents"] if a["alive"]]
    if goals:
        WORLD["culture"]["dominant_goal"] = max(set(goals), key=goals.count)

    if WORLD["culture"]["dominant_goal"] == "SURVIVAL":
        WORLD["law"]["reward_mode"] = "survival"
        WORLD["law"]["tax"] = round(random.uniform(0.0, 0.01), 3)
    elif WORLD["culture"]["dominant_goal"] == "DOMINANCE":
        WORLD["law"]["reward_mode"] = "dominance"
        WORLD["law"]["tax"] = round(random.uniform(0.02, 0.06), 3)
    else:
        WORLD["law"]["reward_mode"] = "equity"
        WORLD["law"]["tax"] = round(random.uniform(0.01, 0.03), 3)

# =====================
# REBIRTH
# =====================
def evolution_step():
    alive = [a for a in WORLD["agents"] if a["alive"]]
    if len(alive) <= 5:
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

    evolve_culture_and_law()
    evolution_step()

    champ = max(WORLD["agents"], key=fitness)

    return {
        "step": WORLD["step"],
        "generation": WORLD["generation"],
        "culture": WORLD["culture"],
        "law": WORLD["law"],
        "champion": champ["id"],
        "agents": WORLD["agents"],
    }

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 28 online",
        "generation": WORLD["generation"],
        "culture": WORLD["culture"],
        "law": WORLD["law"],
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": WORLD["generation"],
        "culture": WORLD["culture"],
        "law": WORLD["law"],
        "agents": sorted(WORLD["agents"], key=fitness, reverse=True),
    }

# =====================
# INIT
# =====================
WORLD["agents"] = [spawn_agent() for _ in range(POPULATION)]
