from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Multi-World Darwinism")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# UTIL
# ==================================================

def uid():
    return str(uuid.uuid4())[:8]

# ==================================================
# AGENT
# ==================================================

def new_agent(name: str) -> Dict:
    return {
        "id": uid(),
        "name": name,
        "hp": 100,
        "fitness": round(random.uniform(0.8, 1.2), 2),
        "alive": True
    }

def agent_vote(agent: Dict, market: Dict):
    if not agent["alive"]:
        return None

    if agent["name"].startswith("HAWK") and market["risk_level"] == "high":
        return "RISK_UP"

    if agent["name"].startswith("DOVE") and market["trend"] == "down":
        return "STABLE"

    if agent["name"].startswith("CHAOS") and market["volatility"] == "extreme":
        return "CHAOS"

    if agent["name"].startswith("HIST") and market["risk_level"] == "high":
        return "CRISIS_PATTERN"

    if agent["name"].startswith("SURV") and market["liquidity"] == "tight":
        return "DEFENSIVE"

    return None

# ==================================================
# WORLD
# ==================================================

def new_world() -> Dict:
    return {
        "id": uid(),
        "stability": 1.0,
        "generation": 1,
        "council": [
            new_agent("HAWK"),
            new_agent("DOVE"),
            new_agent("CHAOS"),
            new_agent("HIST"),
            new_agent("SURV")
        ],
        "history": []
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]

# ==================================================
# MARKET EVAL
# ==================================================

def evaluate_market(market: Dict):
    score = 0.0
    if market["risk_level"] == "high":
        score -= 0.3
    if market["trend"] == "down":
        score -= 0.3
    if market["volatility"] == "extreme":
        score -= 0.2
    if market["liquidity"] == "tight":
        score -= 0.2
    return round(score, 2)

# ==================================================
# DARWINISM
# ==================================================

def apply_agent_darwin(world: Dict, severity: float):
    for agent in world["council"]:
        if not agent["alive"]:
            continue

        if severity > 0.6:
            agent["hp"] -= int(severity * 40)
            agent["fitness"] *= 0.9
        else:
            agent["fitness"] *= 1.05

        if agent["hp"] <= 0:
            agent["alive"] = False

def rebirth_agents(world: Dict):
    for agent in world["council"]:
        if not agent["alive"]:
            agent.update(new_agent(agent["name"] + "_v2"))

def world_decay(world: Dict, severity: float):
    world["stability"] -= severity * 0.5
    world["generation"] += 1

# ==================================================
# MULTI-WORLD EVOLUTION
# ==================================================

def evolve_worlds():
    global WORLDS

    # kill unstable worlds
    WORLDS = [w for w in WORLDS if w["stability"] > 0]

    # rank
    WORLDS.sort(key=lambda w: w["stability"], reverse=True)

    # clone best world if count < 3
    while len(WORLDS) < 3:
        parent = copy.deepcopy(WORLDS[0])
        parent["id"] = uid()
        parent["stability"] *= random.uniform(0.9, 1.1)
        parent["generation"] += 1
        WORLDS.append(parent)

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Multi-World Darwinism Online"}

@app.get("/worlds")
def list_worlds():
    return WORLDS

@app.post("/simulate/market")
def simulate_market(
    risk_level: str = "high",
    trend: str = "down",
    volatility: str = "extreme",
    liquidity: str = "tight"
):
    market = {
        "risk_level": risk_level,
        "trend": trend,
        "volatility": volatility,
        "liquidity": liquidity
    }

    for world in WORLDS:
        votes = []
        for agent in world["council"]:
            vote = agent_vote(agent, market)
            if vote:
                votes.append(vote)

        score = evaluate_market(market)
        severity = abs(score)

        apply_agent_darwin(world, severity)
        rebirth_agents(world)
        world_decay(world, severity)

        world["history"].append({
            "market": market,
            "votes": votes,
            "score": score
        })

    evolve_worlds()

    return {
        "status": "SIMULATION_COMPLETE",
        "market": market,
        "world_rank": sorted(
            [{"id": w["id"], "stability": round(w["stability"], 3)} for w in WORLDS],
            key=lambda x: x["stability"],
            reverse=True
        ),
        "worlds": WORLDS
    }
