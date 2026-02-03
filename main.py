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

app = FastAPI(title="ClawBot Phase 18 – Live Dashboard")

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
# MARKET MODEL (JSON BODY)
# ==================================================

class MarketInput(BaseModel):
    risk_level: str = "high"
    trend: str = "down"
    volatility: str = "extreme"
    liquidity: str = "tight"

# ==================================================
# MARKET LOGIC
# ==================================================

def market_return(m):
    r = 0.0
    if m["trend"] == "up":
        r += random.uniform(0.01, 0.03)
    if m["trend"] == "down":
        r -= random.uniform(0.01, 0.03)
    if m["risk_level"] == "high":
        r -= random.uniform(0.005, 0.015)
    if m["volatility"] == "extreme":
        r += random.uniform(-0.05, 0.05)
    return round(r, 4)

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
    return random.choice(["HOLD", "BUY", "SELL"])

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
        "risk_budget": round(random.uniform(0.15, 0.35), 2),
        "max_dd": round(random.uniform(0.25, 0.45), 2),
        "council": [new_agent("CORE"), new_agent("RISK"), new_agent("EXEC")],
        "history": [],
        "last_return": 0.0,
        "is_champion": False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_HISTORY: List[Dict] = []
CHAMPION_ID = None
STEP = 0

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
    world["equity"] = round(world["cash"] + world["position"], 2)
    world["peak"] = max(world["peak"], world["equity"])
    world["last_return"] = r

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
            "equity": best["equity"]
        })

    CHAMPION_ID = best["id"]
    for w in WORLDS:
        w["is_champion"] = (w["id"] == CHAMPION_ID)

def reproduce():
    global WORLDS
    alive = [w for w in WORLDS if w["alive"]]

    if not alive:
        WORLDS = [new_world()]
        return

    alive.sort(key=lambda w: w["equity"], reverse=True)

    while len(alive) < 3:
        p = copy.deepcopy(alive[0])
        p["id"] = uid()
        p["generation"] += 1
        p["cash"] = p["equity"]
        p["position"] = 0
        p["peak"] = p["cash"]
        p["history"] = []
        p["is_champion"] = False
        alive.append(p)

    WORLDS = alive

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "ClawBot Phase 18 – Running"}

@app.post("/simulate/market")
def simulate_market(market: MarketInput):
    global STEP
    STEP += 1

    m = market.dict()

    select_champion()

    for w in WORLDS:
        if not w["alive"]:
            continue

        signals = [agent_signal(a, m, w["stance"]) for a in w["council"]]
        final_signal = max(set(signals), key=signals.count)

        trade(w, final_signal, m)
        check_death(w)
        w["history"].append(w["equity"])

    reproduce()
    select_champion()

    return {
        "step": STEP,
        "market": m,
        "champion": CHAMPION_ID,
        "worlds": WORLDS
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
            <td>{w['equity']}</td>
            <td>{w['last_return']}</td>
            <td>{"🏆" if w['is_champion'] else ""}</td>
        </tr>
        """

    html = f"""
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
                <th>ID</th><th>Stance</th><th>Gen</th><th>Equity</th><th>Last R</th><th>🏆</th>
            </tr>
            {rows}
        </table>
        <p>Auto refresh every 5s</p>
    </body>
    </html>
    """
    return html
