from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 13 – Self Rule Worlds")

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

def agent_vote(agent: Dict, market: Dict, style: str):
    if not agent["alive"]:
        return None

    if style == "defensive":
        if market["risk_level"] == "high":
            return "CASH"
    if style == "aggressive":
        if market["trend"] == "up":
            return "RISK_ON"
    if style == "volatility":
        if market["volatility"] == "extreme":
            return "VOL_PLAY"

    return None

# ==================================================
# WORLD
# ==================================================

def new_rules():
    return {
        "risk_budget": round(random.uniform(0.05, 0.25), 2),
        "max_drawdown": round(random.uniform(0.15, 0.4), 2),
        "style": random.choice(["defensive", "aggressive", "volatility"])
    }

def new_world(seed_capital: float = 100_000.0) -> Dict:
    return {
        "id": uid(),
        "generation": 1,
        "capital": seed_capital,
        "peak_capital": seed_capital,
        "alive": True,
        "rules": new_rules(),
        "council": [
            new_agent("CORE"),
            new_agent("RISK"),
            new_agent("MEMORY")
        ],
        "history": []
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]

# ==================================================
# MARKET
# ==================================================

def market_severity(m: Dict) -> float:
    score = 0
    if m["risk_level"] == "high":
        score += 0.3
    if m["trend"] == "down":
        score += 0.3
    if m["volatility"] == "extreme":
        score += 0.2
    if m["liquidity"] == "tight":
        score += 0.2
    return round(score, 2)

# ==================================================
# RETURN ENGINE
# ==================================================

def calc_return(votes: List[str], sev: float, rules: Dict):
    base = -sev * rules["risk_budget"]

    if "CASH" in votes:
        base += 0.15
    if "RISK_ON" in votes and sev < 0.4:
        base += 0.25
    if "VOL_PLAY" in votes:
        base += random.uniform(-0.15, 0.25)

    return round(base, 3)

# ==================================================
# EVOLUTION
# ==================================================

def adapt_rules(world: Dict, ret: float):
    rules = world["rules"]

    if ret < 0:
        rules["risk_budget"] *= 0.9
    else:
        rules["risk_budget"] *= 1.05

    rules["risk_budget"] = min(max(rules["risk_budget"], 0.03), 0.4)

def check_death(world: Dict):
    drawdown = 1 - (world["capital"] / world["peak_capital"])
    if drawdown > world["rules"]["max_drawdown"]:
        world["alive"] = False

def reproduce():
    global WORLDS

    survivors = [w for w in WORLDS if w["alive"]]
    if not survivors:
        WORLDS = [new_world()]
        return

    survivors.sort(key=lambda w: w["capital"], reverse=True)

    while len(survivors) < 3:
        parent = copy.deepcopy(survivors[0])
        parent["id"] = uid()
        parent["generation"] += 1
        parent["capital"] *= random.uniform(0.9, 1.1)
        parent["peak_capital"] = parent["capital"]
        parent["rules"] = new_rules()
        survivors.append(parent)

    WORLDS = survivors

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Phase 13 Online – Worlds Self-Optimizing"}

@app.get("/worlds")
def worlds():
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
        if not world["alive"]:
            continue

        votes = []
        for agent in world["council"]:
            v = agent_vote(agent, market, world["rules"]["style"])
            if v:
                votes.append(v)

        ret = calc_return(votes, sev, world["rules"])
        pnl = world["capital"] * ret

        world["capital"] += pnl
        world["peak_capital"] = max(world["peak_capital"], world["capital"])

        adapt_rules(world, ret)
        check_death(world)

        world["history"].append({
            "market": market,
            "votes": votes,
            "return": ret,
            "capital": round(world["capital"], 2),
            "rules": world["rules"]
        })

    reproduce()

    return {
        "market": market,
        "worlds": [
            {
                "id": w["id"],
                "capital": round(w["capital"], 2),
                "rules": w["rules"],
                "alive": w["alive"],
                "generation": w["generation"]
            } for w in WORLDS
        ]
    }
