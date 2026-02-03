from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 16 – Paper Trading Engine")

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
# MARKET MODELS
# ==================================================

VOL_MULTIPLIER = {
    "low": 0.2,
    "normal": 0.5,
    "extreme": 1.0
}

FEE_RATE = 0.001      # 0.1%
BASE_SLIPPAGE = 0.002 # 0.2%

def calc_slippage(volatility: str):
    return BASE_SLIPPAGE * VOL_MULTIPLIER.get(volatility, 0.5)

# ==================================================
# AGENT
# ==================================================

def new_agent(name: str) -> Dict:
    return {"id": uid(), "name": name, "alive": True}

def agent_signal(agent: Dict, market: Dict, stance: str):
    if not agent["alive"]:
        return None

    if stance == "DEFENSIVE" and market["risk_level"] == "high":
        return "SELL"
    if stance == "AGGRESSIVE" and market["trend"] == "up":
        return "BUY"
    if stance == "VOLATILITY" and market["volatility"] == "extreme":
        return "TRADE_VOL"
    return "HOLD"

# ==================================================
# WORLD / PORTFOLIO
# ==================================================

def new_world(seed_capital=100_000):
    return {
        "id": uid(),
        "generation": 1,
        "alive": True,

        # portfolio
        "cash": seed_capital,
        "position": 0.0,
        "equity": seed_capital,
        "peak_equity": seed_capital,

        # risk
        "risk_budget": round(random.uniform(0.1, 0.25), 2),
        "max_drawdown": round(random.uniform(0.25, 0.45), 2),

        # behavior
        "stance": random.choice(["DEFENSIVE", "AGGRESSIVE", "VOLATILITY"]),
        "memory": {},

        # org
        "council": [
            new_agent("CORE"),
            new_agent("RISK"),
            new_agent("EXEC")
        ],

        "history": [],
        "is_champion": False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_ID: str | None = None

# ==================================================
# MARKET ENGINE
# ==================================================

def market_return(market: Dict):
    base = 0
    if market["trend"] == "up":
        base += 0.02
    if market["trend"] == "down":
        base -= 0.02
    if market["risk_level"] == "high":
        base -= 0.01
    if market["volatility"] == "extreme":
        base += random.uniform(-0.03, 0.03)
    return base

# ==================================================
# TRADING ENGINE
# ==================================================

def execute_trade(world: Dict, signal: str, market: Dict):
    price_return = market_return(market)
    slippage = calc_slippage(market["volatility"])

    traded = False
    fee = 0

    if signal == "BUY" and world["cash"] > 0:
        size = world["cash"] * world["risk_budget"]
        fee = size * FEE_RATE
        world["cash"] -= size + fee
        world["position"] += size * (1 - slippage)
        traded = True

    elif signal == "SELL" and world["position"] > 0:
        size = world["position"] * world["risk_budget"]
        fee = size * FEE_RATE
        world["position"] -= size
        world["cash"] += size * (1 - slippage) - fee
        traded = True

    # mark-to-market
    world["position"] *= (1 + price_return)
    world["equity"] = world["cash"] + world["position"]
    world["peak_equity"] = max(world["peak_equity"], world["equity"])

    return {
        "signal": signal,
        "traded": traded,
        "fee": round(fee, 2),
        "slippage": round(slippage, 4),
        "price_return": round(price_return, 4)
    }

# ==================================================
# EVOLUTION
# ==================================================

def check_death(world: Dict):
    dd = 1 - (world["equity"] / world["peak_equity"])
    if dd > world["max_drawdown"]:
        world["alive"] = False

def select_champion():
    global CHAMPION_ID
    alive = [w for w in WORLDS if w["alive"]]
    if not alive:
        CHAMPION_ID = None
        return

    best = max(alive, key=lambda w: w["equity"])
    CHAMPION_ID = best["id"]

    for w in WORLDS:
        w["is_champion"] = (w["id"] == CHAMPION_ID)

def reproduce():
    global WORLDS
    survivors = [w for w in WORLDS if w["alive"]]

    if not survivors:
        WORLDS = [new_world()]
        return

    survivors.sort(key=lambda w: w["equity"], reverse=True)

    while len(survivors) < 3:
        parent = copy.deepcopy(survivors[0])
        parent["id"] = uid()
        parent["generation"] += 1
        parent["cash"] *= random.uniform(0.9, 1.1)
        parent["position"] = 0
        parent["equity"] = parent["cash"]
        parent["peak_equity"] = parent["equity"]
        parent["risk_budget"] *= random.uniform(0.9, 1.1)
        parent["is_champion"] = False
        survivors.append(parent)

    WORLDS = survivors

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Phase 16 Online – Paper Trading Active"}

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

    select_champion()
    champion = next((w for w in WORLDS if w["is_champion"]), None)

    for w in WORLDS:
        if not w["alive"]:
            continue

        aligned = champion and (w["stance"] == champion["stance"])

        signals = []
        for a in w["council"]:
            s = agent_signal(a, market, w["stance"])
            signals.append(s)

        final_signal = max(set(signals), key=signals.count)

        trade = execute_trade(w, final_signal, market)

        if not aligned:
            w["equity"] *= 0.995  # misalignment penalty

        check_death(w)

        w["history"].append({
            "market": market,
            "signals": signals,
            "final_signal": final_signal,
            "trade": trade,
            "equity": round(w["equity"], 2),
            "cash": round(w["cash"], 2),
            "position": round(w["position"], 2),
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
                "equity": round(w["equity"], 2),
                "cash": round(w["cash"], 2),
                "position": round(w["position"], 2),
                "stance": w["stance"],
                "risk_budget": round(w["risk_budget"], 2),
                "alive": w["alive"],
                "generation": w["generation"],
                "is_champion": w["is_champion"]
            } for w in WORLDS
        ]
    }
