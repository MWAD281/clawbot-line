from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import random
import uuid
import copy
import os
import requests
import time

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 17 – Champion Signal Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# LINE CONFIG (OPTIONAL)
# ==================================================

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_USER_ID = os.getenv("LINE_USER_ID", "")  # ใส่ตอนพร้อมใช้งานจริง

# ==================================================
# UTIL
# ==================================================

def uid():
    return str(uuid.uuid4())[:8]

def now():
    return int(time.time())

# ==================================================
# MARKET MODEL
# ==================================================

VOL_MULTIPLIER = {"low": 0.2, "normal": 0.5, "extreme": 1.0}
FEE_RATE = 0.001
BASE_SLIPPAGE = 0.002

def calc_slippage(vol):
    return BASE_SLIPPAGE * VOL_MULTIPLIER.get(vol, 0.5)

def market_return(market):
    r = 0
    if market["trend"] == "up":
        r += 0.02
    if market["trend"] == "down":
        r -= 0.02
    if market["risk_level"] == "high":
        r -= 0.01
    if market["volatility"] == "extreme":
        r += random.uniform(-0.03, 0.03)
    return r

# ==================================================
# AGENTS
# ==================================================

def new_agent(name):
    return {"id": uid(), "name": name, "alive": True}

def agent_signal(agent, market, stance):
    if not agent["alive"]:
        return "HOLD"
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
        "peak_equity": seed,

        "risk_budget": round(random.uniform(0.1, 0.25), 2),
        "max_drawdown": round(random.uniform(0.25, 0.45), 2),

        "stance": random.choice(["DEFENSIVE", "AGGRESSIVE", "VOLATILITY"]),
        "council": [
            new_agent("CORE"),
            new_agent("RISK"),
            new_agent("EXEC")
        ],

        "last_signal": None,
        "last_signal_time": 0,
        "history": [],
        "is_champion": False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_ID = None

# ==================================================
# TRADING
# ==================================================

def execute_trade(world, signal, market):
    r = market_return(market)
    slip = calc_slippage(market["volatility"])
    fee = 0
    traded = False

    if signal == "BUY" and world["cash"] > 0:
        size = world["cash"] * world["risk_budget"]
        fee = size * FEE_RATE
        world["cash"] -= size + fee
        world["position"] += size * (1 - slip)
        traded = True

    elif signal == "SELL" and world["position"] > 0:
        size = world["position"] * world["risk_budget"]
        fee = size * FEE_RATE
        world["position"] -= size
        world["cash"] += size * (1 - slip) - fee
        traded = True

    world["position"] *= (1 + r)
    world["equity"] = world["cash"] + world["position"]
    world["peak_equity"] = max(world["peak_equity"], world["equity"])

    return {
        "signal": signal,
        "traded": traded,
        "return": round(r, 4),
        "fee": round(fee, 2),
        "slippage": round(slip, 4)
    }

# ==================================================
# EVOLUTION
# ==================================================

def check_death(world):
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
        p = copy.deepcopy(survivors[0])
        p["id"] = uid()
        p["generation"] += 1
        p["cash"] *= random.uniform(0.9, 1.1)
        p["position"] = 0
        p["equity"] = p["cash"]
        p["peak_equity"] = p["equity"]
        p["risk_budget"] *= random.uniform(0.9, 1.1)
        p["is_champion"] = False
        p["last_signal"] = None
        p["last_signal_time"] = 0
        survivors.append(p)

    WORLDS = survivors

# ==================================================
# SIGNAL ENGINE (⭐ NEW)
# ==================================================

SIGNAL_COOLDOWN = 300  # seconds

def classify_signal(signal, market):
    if signal == "HOLD":
        return "WATCH"
    if market["volatility"] == "extreme":
        return "ALERT"
    return "ACTION"

def push_line_message(text):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("LINE PUSH (SKIPPED):", text)
        return

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }

    requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=10)

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status": "Phase 17 Online – Champion Signal Active"}

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
    signal_payload = None

    for w in WORLDS:
        if not w["alive"]:
            continue

        signals = [agent_signal(a, market, w["stance"]) for a in w["council"]]
        final_signal = max(set(signals), key=signals.count)

        trade = execute_trade(w, final_signal, market)
        check_death(w)

        w["history"].append({
            "market": market,
            "signals": signals,
            "final_signal": final_signal,
            "equity": round(w["equity"], 2)
        })

        # 🔔 Champion Signal
        if w["is_champion"]:
            if (
                final_signal != w["last_signal"]
                and now() - w["last_signal_time"] > SIGNAL_COOLDOWN
            ):
                level = classify_signal(final_signal, market)
                msg = (
                    f"🏆 CHAMPION SIGNAL [{level}]\n"
                    f"Signal: {final_signal}\n"
                    f"Stance: {w['stance']}\n"
                    f"Market: {market}\n"
                    f"Equity: {round(w['equity'],2)}"
                )
                push_line_message(msg)
                signal_payload = msg

                w["last_signal"] = final_signal
                w["last_signal_time"] = now()

    reproduce()
    select_champion()

    return {
        "market": market,
        "champion": CHAMPION_ID,
        "signal": signal_payload,
        "worlds": [
            {
                "id": w["id"],
                "equity": round(w["equity"], 2),
                "stance": w["stance"],
                "alive": w["alive"],
                "generation": w["generation"],
                "is_champion": w["is_champion"]
            } for w in WORLDS
        ]
    }
