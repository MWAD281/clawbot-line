from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 15 – Champion Brain World")

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
    return {"id": uid(), "name": name, "alive": True}

def agent_vote(agent: Dict, market: Dict, stance: str):
    if not agent["alive"]:
        return None

    if stance == "DEFENSIVE" and market["risk_level"] == "high":
        return "CASH"
    if stance == "AGGRESSIVE" and market["trend"] == "up":
        return "RISK_ON"
    if stance == "VOLATILITY" and market["volatility"] == "extreme":
        return "VOL_PLAY"
    return None

# ==================================================
# CRISIS MEMORY
# ==================================================

CRISIS_LIBRARY = {
    "2008": {
        "pattern": {"liquidity": "tight", "trend": "down"},
        "best_stance": "DEFENSIVE"
    },
    "2020": {
        "pattern": {"volatility": "extreme"},
        "best_stance": "VOLATILITY"
    },
    "2022": {
        "pattern": {"risk_level": "high", "trend": "down"},
        "best_stance": "DEFENSIVE"
    }
}

def detect_crisis(market: Dict):
    hits = []
    for name, crisis in CRISIS_LIBRARY.items():
        if all(market.get(k) == v for k, v in crisis["pattern"].items()):
            hits.append(name)
    return hits

# ==================================================
# WORLD
# ==================================================

def new_world(seed_capital=100_000):
    return {
        "id": uid(),
        "generation": 1,
        "capital": seed_capital,
        "peak": seed_capital,
        "alive": True,
        "risk_budget": round(random.uniform(0.08, 0.25), 2),
        "max_drawdown": round(random.uniform(0.2, 0.4), 2),
        "stance": random.choice(["DEFENSIVE", "AGGRESSIVE", "VOLATILITY"]),
        "memory": {},
        "council": [
            new_agent("CORE"),
            new_agent("RISK"),
            new_agent("MEMORY")
        ],
        "history": [],
        "is_champion": False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_ID: str | None = None

# ==================================================
# MARKET
# ==================================================

def market_severity(m: Dict) -> float:
    score = 0
    score += 0.3 if m["risk_level"] == "high" else 0
    score += 0.3 if m["trend"] == "down" else 0
    score += 0.2 if m["volatility"] == "extreme" else 0
    score += 0.2 if m["liquidity"] == "tight" else 0
    return round(score, 2)

# ==================================================
# RETURN ENGINE
# ==================================================

def calc_return(votes: List[str], sev: float, risk_budget: float, aligned: bool):
    r = -sev * risk_budget
    if "CASH" in votes:
        r += 0.12
    if "RISK_ON" in votes and sev < 0.4:
        r += 0.25
    if "VOL_PLAY" in votes:
        r += random.uniform(-0.1, 0.3)

    # alignment bonus / penalty
    r += 0.05 if aligned else -0.05
    return round(r, 3)

# ==================================================
# EVOLUTION
# ==================================================

def adapt_world(world: Dict, ret: float, crises: List[str]):
    world["risk_budget"] *= 1.05 if ret > 0 else 0.9
    world["risk_budget"] = min(max(world["risk_budget"], 0.05), 0.4)

    for c in crises:
        mem = world["memory"].setdefault(c, {"wins": 0, "losses": 0})
        if ret > 0:
            mem["wins"] += 1
            world["stance"] = CRISIS_LIBRARY[c]["best_stance"]
        else:
            mem["losses"] += 1

def check_death(world: Dict):
    dd = 1 - (world["capital"] / world["peak"])
    if dd > world["max_drawdown"]:
        world["alive"] = False

def select_champion():
    global CHAMPION_ID
    alive = [w for w in WORLDS if w["alive"]]
    if not alive:
        CHAMPION_ID = None
        return

    best = max(alive, key=lambda w: w["capital"])
    CHAMPION_ID = best["id"]

    for w in WORLDS:
        w["is_champion"] = (w["id"] == CHAMPION_ID)

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
        parent["peak"] = parent["capital"]
        parent["risk_budget"] *= random.uniform(0.9, 1.1)
        parent["is_champion"] = False
        survivors.append(parent)

    WORLDS = survivors

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Phase 15 Online – Champion Brain Active"}

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
    crises = detect_crisis(market)

    select_champion()
    champion = next((w for w in WORLDS if w["is_champion"]), None)

    for w in WORLDS:
        if not w["alive"]:
            continue

        aligned = champion and (w["stance"] == champion["stance"])

        votes = []
        for a in w["council"]:
            v = agent_vote(a, market, w["stance"])
            if v:
                votes.append(v)

        ret = calc_return(votes, sev, w["risk_budget"], aligned)
        pnl = w["capital"] * ret

        w["capital"] += pnl
        w["peak"] = max(w["peak"], w["capital"])

        adapt_world(w, ret, crises)
        check_death(w)

        w["history"].append({
            "market": market,
            "crises": crises,
            "votes": votes,
            "aligned_with_champion": aligned,
            "return": ret,
            "capital": round(w["capital"], 2),
            "stance": w["stance"],
            "is_champion": w["is_champion"]
        })

    reproduce()
    select_champion()

    return {
        "market": market,
        "champion": CHAMPION_ID,
        "worlds": [
            {
                "id": w["id"],
                "capital": round(w["capital"], 2),
                "stance": w["stance"],
                "risk_budget": round(w["risk_budget"], 2),
                "alive": w["alive"],
                "generation": w["generation"],
                "is_champion": w["is_champion"],
                "memory": w["memory"]
            } for w in WORLDS
        ]
    }
