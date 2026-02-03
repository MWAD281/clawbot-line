from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 12 – Capital Darwinism")

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
        "fitness": round(random.uniform(0.9, 1.1), 2),
        "alive": True
    }

def agent_vote(agent: Dict, market: Dict):
    if not agent["alive"]:
        return None

    if agent["name"].startswith("HAWK") and market["risk_level"] == "high":
        return "RISK_ON"
    if agent["name"].startswith("DOVE") and market["trend"] == "down":
        return "DEFENSIVE"
    if agent["name"].startswith("CHAOS") and market["volatility"] == "extreme":
        return "VOL_PLAY"
    if agent["name"].startswith("HIST") and market["risk_level"] == "high":
        return "CRISIS_MEMORY"
    if agent["name"].startswith("SURV") and market["liquidity"] == "tight":
        return "CASH"

    return None

# ==================================================
# WORLD
# ==================================================

def new_world(seed_capital: float = 100_000.0) -> Dict:
    return {
        "id": uid(),
        "generation": 1,
        "stability": 1.0,
        "capital": seed_capital,
        "return_pct": 0.0,
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

def market_severity(market: Dict) -> float:
    sev = 0.0
    if market["risk_level"] == "high":
        sev += 0.3
    if market["trend"] == "down":
        sev += 0.3
    if market["volatility"] == "extreme":
        sev += 0.2
    if market["liquidity"] == "tight":
        sev += 0.2
    return round(sev, 2)

# ==================================================
# CAPITAL LOGIC
# ==================================================

def capital_outcome(votes: List[str], severity: float) -> float:
    """
    ผลตอบแทนโดยคร่าว:
    - defensive / cash ช่วยลด drawdown
    - risk_on ในตลาดรุนแรง = เจ็บ
    """
    base = -severity

    if "DEFENSIVE" in votes:
        base += 0.15
    if "CASH" in votes:
        base += 0.2
    if "RISK_ON" in votes and severity > 0.5:
        base -= 0.2
    if "VOL_PLAY" in votes:
        base += random.uniform(-0.1, 0.1)

    return round(base, 3)

# ==================================================
# DARWINISM
# ==================================================

def evolve_agents(world: Dict, severity: float):
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

def rebirth(world: Dict):
    for agent in world["council"]:
        if not agent["alive"]:
            agent.update(new_agent(agent["name"] + "_v2"))

def world_decay(world: Dict, severity: float):
    world["stability"] -= severity * 0.4
    world["generation"] += 1

# ==================================================
# MULTI-WORLD SELECTION
# ==================================================

def evolve_worlds():
    global WORLDS

    # ลบโลกที่เงินหมดหรือเสถียรภาพพัง
    WORLDS = [w for w in WORLDS if w["capital"] > 10_000 and w["stability"] > 0]

    WORLDS.sort(key=lambda w: (w["capital"], w["stability"]), reverse=True)

    # clone โลกที่เก่ง
    while len(WORLDS) < 3:
        parent = copy.deepcopy(WORLDS[0])
        parent["id"] = uid()
        parent["generation"] += 1
        parent["capital"] *= random.uniform(0.9, 1.05)
        parent["stability"] *= random.uniform(0.9, 1.1)
        WORLDS.append(parent)

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Phase 12 Capital Darwinism Online"}

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

    sev = market_severity(market)

    for world in WORLDS:
        votes = []
        for agent in world["council"]:
            v = agent_vote(agent, market)
            if v:
                votes.append(v)

        ret = capital_outcome(votes, sev)
        pnl = world["capital"] * ret

        world["capital"] += pnl
        world["return_pct"] = ret

        evolve_agents(world, sev)
        rebirth(world)
        world_decay(world, sev)

        world["history"].append({
            "market": market,
            "votes": votes,
            "return_pct": ret,
            "capital": round(world["capital"], 2)
        })

    evolve_worlds()

    return {
        "status": "SIMULATION_COMPLETE",
        "market": market,
        "world_rank": [
            {
                "id": w["id"],
                "capital": round(w["capital"], 2),
                "stability": round(w["stability"], 3),
                "generation": w["generation"]
            }
            for w in sorted(WORLDS, key=lambda x: x["capital"], reverse=True)
        ]
    }
