from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid

app = FastAPI(title="ClawBot Phase 30 – World War Darwinism")

# ==================================================
# CORS
# ==================================================
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
BASE_CAPITAL = 100_000
POPULATION = 12
MAX_WORLDS = 5
EXTINCTION = 0.4
WAR_THRESHOLD = 1.2  # world score > 1.2x opponent = can attack

WORLD_TYPES = ["crypto", "equity", "macro"]
TRENDS = ["up", "down", "side"]
GOALS = ["SURVIVAL", "GROWTH", "DOMINANCE"]

# ==================================================
# DNA
# ==================================================
def gene():
    return {
        "risk": round(random.uniform(0.01, 0.3), 3),
        "leverage": round(random.uniform(1, 20), 2),
        "aggression": round(random.uniform(0.2, 4.0), 2),
    }

def random_dna():
    return {
        "strategy": {
            w: {t: gene() for t in TRENDS}
            for w in WORLD_TYPES
        },
        "meta": {
            "mutation": round(random.uniform(0.2, 0.8), 2),
            "chaos": round(random.uniform(0.0, 2.0), 2),
        }
    }

def mutate_dna(dna):
    new = {"strategy": {}, "meta": dna["meta"].copy()}
    for k in new["meta"]:
        if random.random() < 0.4:
            new["meta"][k] = round(
                max(0.1, min(2.5, new["meta"][k] + random.uniform(-0.3, 0.3))), 2
            )

    for w in dna["strategy"]:
        new["strategy"][w] = {}
        for t in dna["strategy"][w]:
            g = dna["strategy"][w][t].copy()
            if random.random() < new["meta"]["mutation"]:
                g["risk"] = round(max(0.005, min(0.5, g["risk"] + random.uniform(-0.05, 0.05))), 3)
            if random.random() < new["meta"]["mutation"]:
                g["leverage"] = round(max(1, min(30, g["leverage"] + random.uniform(-5, 5))), 2)
            if random.random() < new["meta"]["mutation"]:
                g["aggression"] = round(max(0.1, min(6.0, g["aggression"] + random.uniform(-1, 1))), 2)
            new["strategy"][w][t] = g
    return new

# ==================================================
# AGENT
# ==================================================
def spawn_agent(dna=None):
    return {
        "id": uuid.uuid4().hex[:8],
        "alive": True,
        "equity": BASE_CAPITAL,
        "peak": BASE_CAPITAL,
        "dna": dna or random_dna(),
        "goal": random.choice(GOALS),
        "score": 0.0,
    }

def fitness(a):
    dd = (a["peak"] - a["equity"]) / max(a["peak"], 1)
    if a["goal"] == "SURVIVAL":
        return a["equity"] * (1 - dd * 2)
    if a["goal"] == "DOMINANCE":
        return a["score"]
    return a["equity"]

# ==================================================
# WORLD
# ==================================================
def spawn_world(seed_dna=None):
    return {
        "id": uuid.uuid4().hex[:6],
        "agents": [
            spawn_agent(mutate_dna(seed_dna) if seed_dna else None)
            for _ in range(POPULATION)
        ],
        "law": {
            "tax": round(random.uniform(0.01, 0.05), 3),
            "military": round(random.uniform(0.5, 2.0), 2),
        },
        "culture": {
            "goal": random.choice(GOALS),
        },
        "alive": True,
        "age": 0,
        "score": 0.0,
    }

# ==================================================
# MULTIVERSE
# ==================================================
MULTIVERSE: List[Dict] = [spawn_world() for _ in range(2)]
STEP = 0

# ==================================================
# SIMULATION
# ==================================================
def simulate_agent(a, market, world):
    if not a["alive"]:
        return

    g = a["dna"]["strategy"][market["world"]][market["trend"]]
    chaos = random.uniform(-1, 1) * a["dna"]["meta"]["chaos"]

    intent = 1.0
    if a["goal"] == "SURVIVAL":
        intent = 0.6
    elif a["goal"] == "DOMINANCE":
        intent = 1.4

    pnl = a["equity"] * g["risk"] * g["leverage"] * g["aggression"] * intent * (random.uniform(-1,1) + chaos) * 0.01
    tax = abs(pnl) * world["law"]["tax"]

    a["equity"] += pnl - tax
    a["score"] += pnl

    if a["equity"] > a["peak"]:
        a["peak"] = a["equity"]

    if a["equity"] < BASE_CAPITAL * EXTINCTION:
        a["alive"] = False

def simulate_world(w, market):
    if not w["alive"]:
        return

    w["age"] += 1
    for a in w["agents"]:
        simulate_agent(a, market, w)

    alive = [a for a in w["agents"] if a["alive"]]
    if not alive:
        w["alive"] = False
        return

    champ = max(alive, key=fitness)
    w["culture"]["goal"] = champ["goal"]
    w["score"] = sum(a["equity"] for a in alive)

# ==================================================
# WAR SYSTEM
# ==================================================
def world_war():
    alive_worlds = [w for w in MULTIVERSE if w["alive"]]
    if len(alive_worlds) < 2:
        return

    attacker = max(alive_worlds, key=lambda w: w["score"])
    defender = min(alive_worlds, key=lambda w: w["score"])

    if attacker["score"] < defender["score"] * WAR_THRESHOLD:
        return

    # WAR!
    power_a = attacker["score"] * attacker["law"]["military"]
    power_d = defender["score"] * defender["law"]["military"]

    if power_a > power_d:
        # attacker wins – steal best DNA
        victim_agents = [a for a in defender["agents"] if a["alive"]]
        if victim_agents:
            stolen = max(victim_agents, key=fitness)
            attacker["agents"].append(spawn_agent(stolen["dna"]))
        defender["alive"] = False
    else:
        attacker["alive"] = False

# ==================================================
# EVOLUTION
# ==================================================
def evolve():
    global MULTIVERSE
    alive = [w for w in MULTIVERSE if w["alive"]]

    if not alive:
        MULTIVERSE = [spawn_world()]
        return

    if len(alive) < MAX_WORLDS:
        parent = max(alive, key=lambda w: w["score"])
        champ = max(parent["agents"], key=fitness)
        MULTIVERSE.append(spawn_world(seed_dna=champ["dna"]))

# ==================================================
# API
# ==================================================
@app.post("/simulate/market")
def simulate_market(market: Dict):
    global STEP
    STEP += 1

    for w in MULTIVERSE:
        simulate_world(w, market)

    world_war()
    evolve()

    return {
        "step": STEP,
        "worlds": [
            {
                "id": w["id"],
                "alive": w["alive"],
                "score": round(w["score"], 2),
                "agents": len([a for a in w["agents"] if a["alive"]]),
                "culture": w["culture"],
            }
            for w in MULTIVERSE
        ]
    }

@app.get("/")
def root():
    return {
        "status": "Phase 30 – World War Active",
        "step": STEP,
        "worlds": len(MULTIVERSE)
    }

@app.get("/dashboard")
def dashboard():
    return {
        "step": STEP,
        "multiverse": MULTIVERSE
    }
