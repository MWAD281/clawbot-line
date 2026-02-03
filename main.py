from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List
import random
import time
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 94.5 – Production Safe Core",
    version="94.5.0",
    description="Testnet-ready + per-agent risk guard + smart sizing"
)

# =========================
# GLOBAL CONFIG
# =========================

PHASE = 94.5
MAX_AGENTS = 5

INITIAL_CAPITAL = 100_000.0
MAX_RISK_PER_TRADE = 0.02        # 2% ต่อไม้
MAX_AGENT_DRAWDOWN = -0.20       # agent ใดขาดทุน 20% = ตาย
STOP_LOSS_PCT = 0.03
TAKE_PROFIT_PCT = 0.06
MIN_FITNESS = 0.55
MUTATION_RATE = 0.10
GLOBAL_MAX_DRAWDOWN = -0.30

AGENTS: Dict[int, Dict] = {}
TRADE_LOG: List[Dict] = []

# =========================
# MODELS
# =========================

class MarketInput(BaseModel):
    price: float = 100.0
    exchange: str = "sandbox"   # sandbox | binance_testnet | bybit_testnet


class TradeResult(BaseModel):
    trade_id: str
    agent_id: int
    decision: str
    size: float
    entry_price: float
    exit_price: float
    pnl: float
    capital_after: float
    fitness: float
    note: str
    timestamp: float

# =========================
# AGENT CORE
# =========================

def create_genome():
    return {
        "risk": round(random.uniform(0.2, 0.8), 2),
        "aggression": round(random.uniform(0.2, 0.8), 2),
        "patience": round(random.uniform(0.2, 0.8), 2),
    }


def spawn_agent(agent_id: int):
    AGENTS[agent_id] = {
        "genome": create_genome(),
        "fitness": round(random.uniform(0.6, 0.8), 3),
        "capital": INITIAL_CAPITAL / MAX_AGENTS,
        "peak_capital": INITIAL_CAPITAL / MAX_AGENTS,
        "alive": True,
        "wins": 0,
        "losses": 0,
        "trades": 0
    }


for i in range(1, MAX_AGENTS + 1):
    spawn_agent(i)

# =========================
# CEO COUNCIL
# =========================

def ceo_optimist(d, c): return d if c > 0.6 else "HOLD"
def ceo_pessimist(d, c): return d if c > 0.75 else "HOLD"
def ceo_realist(d, c): return d if 0.55 <= c <= 0.8 else "HOLD"
def ceo_strategist(d, c): return d if c > 0.65 else "HOLD"

CEO_COUNCIL = {
    "optimist": ceo_optimist,
    "pessimist": ceo_pessimist,
    "realist": ceo_realist,
    "strategist": ceo_strategist,
}

# =========================
# UTILS
# =========================

def global_drawdown():
    total = sum(a["capital"] for a in AGENTS.values())
    return (total - INITIAL_CAPITAL) / INITIAL_CAPITAL


def agent_drawdown(agent):
    return (agent["capital"] - agent["peak_capital"]) / agent["peak_capital"]


def agent_decide(genome):
    r = random.random()
    if r < genome["aggression"]:
        return "BUY"
    if r > 1 - genome["risk"]:
        return "SELL"
    return "HOLD"


def position_size(capital, confidence):
    base = capital * MAX_RISK_PER_TRADE
    scaled = base * min(confidence, 0.9)
    return round(scaled, 2)


def update_fitness(agent, pnl):
    agent["fitness"] = round(
        max(0.0, min(1.0, agent["fitness"] + pnl / max(agent["capital"], 1))),
        3
    )


def maybe_mutate(genome):
    if random.random() < MUTATION_RATE:
        k = random.choice(list(genome.keys()))
        genome[k] = round(
            max(0.1, min(0.9, genome[k] + random.uniform(-0.15, 0.15))), 2
        )
        return f"mutation:{k}"
    return None

# =========================
# EXCHANGE ADAPTER (SAFE)
# =========================

def execute_trade(exchange, decision, price, size):
    if decision == "HOLD":
        return price, price, 0.0

    entry = price * (1 + random.uniform(-0.001, 0.001))
    move = random.uniform(-0.07, 0.08)
    raw_exit = entry * (1 + move)

    sl = entry * (1 - STOP_LOSS_PCT)
    tp = entry * (1 + TAKE_PROFIT_PCT)

    exit_price = min(max(raw_exit, sl), tp)
    pnl = (exit_price - entry) / entry * size

    return round(entry, 4), round(exit_price, 4), round(pnl, 2)

# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": PHASE,
        "agents_alive": sum(1 for a in AGENTS.values() if a["alive"]),
        "drawdown": round(global_drawdown(), 3),
        "trades": len(TRADE_LOG)
    }


@app.get("/health")
def health():
    return {"ok": True, "phase": PHASE}

# =========================
# CORE SIMULATION
# =========================

@app.post("/simulate/market", response_model=TradeResult)
def simulate_market(input: MarketInput):

    if global_drawdown() <= GLOBAL_MAX_DRAWDOWN:
        return TradeResult(
            trade_id="HALT",
            agent_id=-1,
            decision="HALT",
            size=0,
            entry_price=0,
            exit_price=0,
            pnl=0,
            capital_after=sum(a["capital"] for a in AGENTS.values()),
            fitness=0,
            note="GLOBAL KILL SWITCH",
            timestamp=time.time()
        )

    alive = [i for i, a in AGENTS.items() if a["alive"]]
    agent_id = random.choice(alive)
    agent = AGENTS[agent_id]

    genome = agent["genome"]
    decision = agent_decide(genome)
    confidence = random.uniform(0.5, 0.95)

    votes = {k: f(decision, confidence) for k, f in CEO_COUNCIL.items()}
    final_decision = max(set(votes.values()), key=lambda d: list(votes.values()).count(d))

    size = position_size(agent["capital"], confidence)
    entry, exit_p, pnl = execute_trade(
        input.exchange, final_decision, input.price, size
    )

    agent["capital"] += pnl
    agent["peak_capital"] = max(agent["peak_capital"], agent["capital"])
    agent["trades"] += 1

    if pnl > 0:
        agent["wins"] += 1
    else:
        agent["losses"] += 1

    update_fitness(agent, pnl)

    note = "ok"

    if agent_drawdown(agent) <= MAX_AGENT_DRAWDOWN or agent["fitness"] < MIN_FITNESS:
        agent["alive"] = False
        spawn_agent(agent_id)
        note = "agent killed → reborn (risk)"

    mut = maybe_mutate(genome)
    if mut:
        note += f" | {mut}"

    trade = {
        "id": str(uuid.uuid4()),
        "agent": agent_id,
        "decision": final_decision,
        "entry": entry,
        "exit": exit_p,
        "pnl": pnl,
        "capital": agent["capital"],
        "time": time.time()
    }
    TRADE_LOG.append(trade)

    return TradeResult(
        trade_id=trade["id"],
        agent_id=agent_id,
        decision=final_decision,
        size=size,
        entry_price=entry,
        exit_price=exit_p,
        pnl=pnl,
        capital_after=round(agent["capital"], 2),
        fitness=agent["fitness"],
        note=note,
        timestamp=trade["time"]
    )

# =========================
# RANKING / MONITOR
# =========================

@app.get("/ranking")
def ranking():
    ranked = sorted(
        AGENTS.items(),
        key=lambda x: (
            x[1]["fitness"],
            x[1]["capital"],
            x[1]["wins"] - x[1]["losses"]
        ),
        reverse=True
    )
    return {
        "phase": PHASE,
        "ranking": [
            {
                "agent": i,
                "fitness": a["fitness"],
                "capital": round(a["capital"], 2),
                "wins": a["wins"],
                "losses": a["losses"],
                "trades": a["trades"]
            }
            for i, a in ranked
        ]
    }


@app.get("/trades")
def trades():
    return TRADE_LOG[-50:]


@app.post("/reset")
def reset():
    AGENTS.clear()
    TRADE_LOG.clear()
    for i in range(1, MAX_AGENTS + 1):
        spawn_agent(i)
    return {"reset": True, "phase": PHASE}
