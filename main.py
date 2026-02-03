from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List
import random
import time
import copy
import uuid

app = FastAPI(
    title="ClawBot Phase 91 – Sandbox Execution",
    version="91.0.0",
    description="Decision engine + sandbox exchange + trade logging"
)

# =========================
# GLOBAL CONFIG
# =========================

PHASE = 91
GENERATION = 91

MAX_AGENTS = 5
MIN_FITNESS = 0.55
MUTATION_RATE = 0.12

INITIAL_CAPITAL = 100_000.0
GLOBAL_MAX_DRAWDOWN = -0.30
MAX_RISK_PER_TRADE = 0.15

AGENTS: Dict[int, Dict] = {}
TRADE_LOG: List[Dict] = []

# =========================
# MODELS
# =========================

class MarketInput(BaseModel):
    price: Optional[float] = 100.0
    volatility: Optional[str] = "normal"
    regime: Optional[str] = "neutral"


class TradeResult(BaseModel):
    trade_id: str
    agent_id: int
    decision: str
    executed_price: float
    size: float
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
        "alive": True,
        "history": []
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
    current = sum(a["capital"] for a in AGENTS.values())
    return (current - INITIAL_CAPITAL) / INITIAL_CAPITAL


def agent_decide(genome):
    r = random.random()
    if r < genome["aggression"]:
        return "BUY"
    if r > 1 - genome["risk"]:
        return "SELL"
    return "HOLD"


def update_fitness(agent, pnl):
    agent["fitness"] = round(
        max(0.0, min(1.0, agent["fitness"] + pnl)),
        3
    )
    agent["history"].append(agent["fitness"])
    if len(agent["history"]) > 30:
        agent["history"].pop(0)


def maybe_mutate(genome):
    if random.random() < MUTATION_RATE:
        k = random.choice(list(genome.keys()))
        genome[k] = round(
            max(0.1, min(0.9, genome[k] + random.uniform(-0.15, 0.15))), 2
        )
        return f"mutation:{k}"
    return None

# =========================
# SANDBOX EXCHANGE
# =========================

def sandbox_execute(decision, price, capital):
    if decision == "HOLD":
        return price, 0.0, 0.0

    size = capital * MAX_RISK_PER_TRADE
    slippage = random.uniform(-0.002, 0.002)
    executed_price = round(price * (1 + slippage), 4)

    move = random.uniform(-0.04, 0.05)
    pnl = size * move

    return executed_price, size, round(pnl, 2)

# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": PHASE,
        "agents": len(AGENTS),
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
            executed_price=0,
            size=0,
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
    confidence = round(random.uniform(0.5, 0.95), 2)

    votes = {k: f(decision, confidence) for k, f in CEO_COUNCIL.items()}
    final_decision = max(set(votes.values()), key=lambda d: list(votes.values()).count(d))

    exec_price, size, pnl = sandbox_execute(
        final_decision, input.price, agent["capital"]
    )

    agent["capital"] += pnl
    update_fitness(agent, pnl / max(agent["capital"], 1))

    note = "ok"
    if agent["fitness"] < MIN_FITNESS:
        agent["alive"] = False
        spawn_agent(agent_id)
        note = "agent died → reborn"

    mut = maybe_mutate(genome)
    if mut:
        note += f" | {mut}"

    trade = {
        "id": str(uuid.uuid4()),
        "agent": agent_id,
        "decision": final_decision,
        "price": exec_price,
        "size": size,
        "pnl": pnl,
        "capital": agent["capital"],
        "time": time.time()
    }
    TRADE_LOG.append(trade)

    return TradeResult(
        trade_id=trade["id"],
        agent_id=agent_id,
        decision=final_decision,
        executed_price=exec_price,
        size=size,
        pnl=pnl,
        capital_after=round(agent["capital"], 2),
        fitness=agent["fitness"],
        note=note,
        timestamp=trade["time"]
    )

# =========================
# DEBUG
# =========================

@app.get("/agents")
def agents():
    return AGENTS


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
