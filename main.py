from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List
import random
import uuid
import copy
import time

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 18 – Live Darwinism")

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

def now():
    return int(time.time())

# ==================================================
# MARKET
# ==================================================

def market_return(m):
    r = 0.0
    if m["trend"] == "up":
        r += 0.02
    if m["trend"] == "down":
        r -= 0.02
    if m["risk_level"] == "high":
        r -= 0.01
    if m["volatility"] == "extreme":
        r += random.uniform(-0.03, 0.03)
    return r

# ==================================================
# AGENTS
# ==================================================

def new_agent(name):
    return {"id": uid(), "name": name}

def agent_signal(agent, market, stance):
    if stance == "DEFENSIVE" and market["risk_level"] == "high":
        return "SELL"
    if stance == "AGGRESSIVE" and market["trend"] == "up":
        return "BUY"
    if stance == "VOLATILITY" and market["volatility"] == "extreme":
        return random.choice(["BUY", "SELL"])
    return "HOLD"

# ==================================================
# WORLD
# ==================================================

def new_world(seed=100_000):
    return {
        "id": uid(),
        "generation": 1,
        "alive": True,
        "cash": seed,
        "position": 0.0,
        "equity": seed,
        "peak": seed,
        "stance": random.choice(["DEFENSIVE", "AGGRESSIVE", "VOLATILITY"]),
        "risk_budget": round(random.uniform(0.1, 0.25), 2),
        "max_dd": round(random.uniform(0.25, 0.45), 2),
        "council": [
            new_agent("CORE"),
            new_agent("RISK"),
            new_agent("EXEC")
        ],
        "history": [],
        "is_champion": False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_HISTORY: List[Dict] = []
CHAMPION_ID = None

# ==================================================
# TRADING
# ==================================================

def trade(world, signal, market):
    r = market_return(market)

    if signal == "BUY" and world["cash"] > 0:
        size = world["cash"] * world["risk_budget"]
        world["cash"] -= size
        world["position"] += size

    elif signal == "SELL" and world["position"] > 0:
        size = world["position"] * world["risk_budget"]
        world["position"] -= size
        world["cash"] += size

    world["position"] *= (1 + r)
    world["equity"] = world["cash"] + world["position"]
    world["peak"] = max(world["peak"], world["equity"])

def check_death(world):
    dd = 1 - (world["equity"] / world["peak"])
    if dd > world["max_dd"]:
        world["alive"] = False

# ==================================================
# EVOLUTION
# ==================================================

def select_champion():
    global CHAMPION_ID

    alive = [w for w in WORLDS if w["alive"]]
    if not alive:
        CHAMPION_ID = None
        return

    best = max(alive, key=lambda w: w["equity"])

    if CHAMPION_ID != best["id"]:
        CHAMPION_HISTORY.append({
            "time": now(),
            "champion": best["id"],
            "equity": round(best["equity"], 2)
        })

    CHAMPION_ID = best["id"]

    for w in WORLDS:
        w["is_champion"] = (w["id"] == CHAMPION_ID)

def reproduce():
    global WORLDS

    alive = [w for w in WORLDS if w["alive"]]

    if not alive:
        WORLDS = [new_world() for _ in range(3)]
        return

    alive.sort(key=lambda w: w["equity"], reverse=True)

    children = alive.copy()
    while len(children) < 3:
        parent = copy.deepcopy(alive[0])
        parent["id"] = uid()
        parent["generation"] += 1
        parent["cash"] = parent["equity"]
        parent["position"] = 0
        parent["peak"] = parent["cash"]
        parent["history"] = []
        parent["alive"] = True
        parent["is_champion"] = False
        children.append(parent)

    WORLDS = children

# ==================================================
# API MODELS
# ==================================================

class MarketInput(BaseModel):
    risk_level: str = "high"
    trend: str = "down"
    volatility: str = "extreme"
    liquidity: str = "tight"

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 18 – Running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/simulate/market")
def simulate_market(market: MarketInput):
    market = market.dict()

    select_champion()

    for w in WORLDS:
        if not w["alive"]:
            continue

        signals = [
            agent_signal(a, market, w["stance"])
            for a in w["council"]
        ]
        final_signal = max(set(signals), key=signals.count)

        trade(w, final_signal, market)
        check_death(w)
        w["history"].append(round(w["equity"], 2))

    reproduce()
    select_champion()

    return {
        "status": "SIMULATION_COMPLETE",
        "market": market,
        "champion": CHAMPION_ID,
        "worlds": [
            {
                "id": w["id"],
                "equity": round(w["equity"], 2),
                "stance": w["stance"],
                "alive": w["alive"],
                "gen": w["generation"],
                "is_champion": w["is_champion"]
            } for w in WORLDS
        ]
    }

# ==================================================
# DASHBOARD
# ==================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    rows = ""
    for w in WORLDS:
        rows += f"""
        <tr>
            <td>{w['id']}</td>
            <td>{w['stance']}</td>
            <td>{w['generation']}</td>
            <td>{round(w['equity'],2)}</td>
            <td>{"🏆" if w['is_champion'] else ""}</td>
        </tr>
        """

    champ_hist = "".join(
        f"<li>{h['time']} → {h['champion']} ({h['equity']})</li>"
        for h in CHAMPION_HISTORY[-10:]
    )

    return f"""
    <html>
    <head>
        <title>ClawBot Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial; background:#0e1117; color:#e6e6e6 }}
            table {{ border-collapse: collapse; width:100% }}
            th, td {{ border:1px solid #333; padding:8px; text-align:center }}
            th {{ background:#1f2933 }}
        </style>
    </head>
    <body>
        <h1>🧠 ClawBot Live Dashboard</h1>
        <table>
            <tr>
                <th>ID</th><th>Stance</th><th>Gen</th><th>Equity</th><th>Champion</th>
            </tr>
            {rows}
        </table>

        <h2>🏆 Champion Timeline</h2>
        <ul>{champ_hist}</ul>
        <p>Auto refresh every 5s</p>
    </body>
    </html>
    """
