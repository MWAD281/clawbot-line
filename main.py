from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, List
import random, uuid, copy, time, threading

# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Phase 20 – AutoRun Regime Shift")

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

def uid(): return str(uuid.uuid4())[:8]
def now(): return int(time.time())
def clamp(v, lo, hi): return max(lo, min(v, hi))

# ==================================================
# MARKET (Regime Engine)
# ==================================================

REGIMES = [
    {"trend":"up","risk":"low","vol":"normal"},
    {"trend":"down","risk":"high","vol":"normal"},
    {"trend":"side","risk":"medium","vol":"low"},
    {"trend":"up","risk":"medium","vol":"extreme"},
    {"trend":"down","risk":"high","vol":"extreme"},
]

CURRENT_REGIME = random.choice(REGIMES)
LAST_SHIFT = now()
SHIFT_INTERVAL = 20  # seconds

def maybe_shift_regime():
    global CURRENT_REGIME, LAST_SHIFT
    if now() - LAST_SHIFT > SHIFT_INTERVAL:
        CURRENT_REGIME = random.choice(REGIMES)
        LAST_SHIFT = now()

def market_return():
    r = 0
    if CURRENT_REGIME["trend"] == "up": r += 0.02
    if CURRENT_REGIME["trend"] == "down": r -= 0.02
    if CURRENT_REGIME["vol"] == "extreme": r += random.uniform(-0.06,0.06)
    if CURRENT_REGIME["risk"] == "high": r -= 0.01
    return r

# ==================================================
# AGENTS
# ==================================================

def new_agent(name): return {"id":uid(),"name":name}

def agent_signal(market, stance):
    if stance=="DEFENSIVE" and market["risk"]=="high": return "SELL"
    if stance=="AGGRESSIVE" and market["trend"]=="up": return "BUY"
    if stance=="VOLATILITY" and market["vol"]=="extreme":
        return random.choice(["BUY","SELL"])
    return "HOLD"

# ==================================================
# WORLD
# ==================================================

def new_world(seed=100_000):
    return {
        "id":uid(),
        "gen":1,
        "alive":True,
        "cash":seed,
        "pos":0.0,
        "equity":seed,
        "peak":seed,
        "stance":random.choice(["DEFENSIVE","AGGRESSIVE","VOLATILITY"]),
        "risk":round(random.uniform(0.1,0.3),2),
        "max_dd":round(random.uniform(0.25,0.45),2),
        "last_r":0.0,
        "council":[new_agent("CORE"),new_agent("RISK"),new_agent("EXEC")],
        "champ":False
    }

WORLDS: List[Dict] = [new_world() for _ in range(3)]
CHAMPION_ID = None
STEP = 0

# ==================================================
# CORE LOGIC
# ==================================================

def trade(w):
    before = w["equity"]
    r = market_return()

    sigs = [agent_signal(CURRENT_REGIME, w["stance"]) for _ in w["council"]]
    signal = max(set(sigs), key=sigs.count)

    if signal=="BUY" and w["cash"]>0:
        size = w["cash"]*w["risk"]
        w["cash"]-=size; w["pos"]+=size
    elif signal=="SELL" and w["pos"]>0:
        size = w["pos"]*w["risk"]
        w["pos"]-=size; w["cash"]+=size

    w["pos"]*=(1+r)
    w["equity"]=w["cash"]+w["pos"]
    w["peak"]=max(w["peak"],w["equity"])
    w["last_r"]=round((w["equity"]-before)/before,4)

def check_death(w):
    dd = 1-(w["equity"]/w["peak"])
    if dd>w["max_dd"]: w["alive"]=False

def fitness(w):
    dd = 1-(w["equity"]/w["peak"])
    return w["last_r"]-dd

def mutate(parent):
    w = copy.deepcopy(parent)
    w["id"]=uid(); w["gen"]+=1
    w["risk"]=clamp(w["risk"]+random.uniform(-0.05,0.05),0.05,0.4)
    w["max_dd"]=clamp(w["max_dd"]+random.uniform(-0.05,0.05),0.15,0.6)
    if random.random()<0.2:
        w["stance"]=random.choice(["DEFENSIVE","AGGRESSIVE","VOLATILITY"])
    w["cash"]=w["equity"]; w["pos"]=0; w["peak"]=w["cash"]
    w["alive"]=True; w["champ"]=False
    return w

def evolve():
    global WORLDS, CHAMPION_ID
    alive=[w for w in WORLDS if w["alive"]]
    if not alive:
        WORLDS=[new_world()]; return
    alive.sort(key=fitness, reverse=True)
    champ=alive[0]["id"]
    for w in alive: w["champ"]=(w["id"]==champ)
    CHAMPION_ID=champ
    while len(alive)<3:
        alive.append(mutate(alive[0]))
    WORLDS=alive

# ==================================================
# AUTO RUN LOOP
# ==================================================

AUTO_INTERVAL = 3  # seconds

def auto_loop():
    global STEP
    while True:
        time.sleep(AUTO_INTERVAL)
        STEP+=1
        maybe_shift_regime()
        for w in WORLDS:
            if not w["alive"]: continue
            trade(w); check_death(w)
        evolve()

threading.Thread(target=auto_loop, daemon=True).start()

# ==================================================
# API
# ==================================================

@app.get("/")
def root():
    return {"status":"ClawBot Phase 20 running","step":STEP,"regime":CURRENT_REGIME}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    rows=""
    for w in WORLDS:
        rows+=f"""
        <tr>
            <td>{w['id']}</td><td>{w['stance']}</td><td>{w['gen']}</td>
            <td>{round(w['equity'],2)}</td><td>{w['last_r']}</td>
            <td>{"🏆" if w['champ'] else ""}</td>
        </tr>
        """
    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="5">
        <style>
            body{{background:#0e1117;color:#e6e6e6;font-family:Arial}}
            table{{width:100%;border-collapse:collapse}}
            th,td{{border:1px solid #333;padding:8px;text-align:center}}
            th{{background:#1f2933}}
        </style>
    </head>
    <body>
        <h1>🧬 ClawBot Phase 20 – Auto Evolution</h1>
        <p>Regime: {CURRENT_REGIME}</p>
        <table>
            <tr><th>ID</th><th>Stance</th><th>Gen</th><th>Equity</th><th>Last R</th><th>🏆</th></tr>
            {rows}
        </table>
    </body>
    </html>
    """
