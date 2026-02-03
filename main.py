from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional
import random
import time
import copy

app = FastAPI(
    title="ClawBot Phase 90 – CEO Council (Hardened)",
    version="90.1.0",
    description="Multi-CEO voting, Darwinism, capital, global risk guard"
)

# =========================
# GLOBAL CONFIG
# =========================

GENERATION = 90

MAX_AGENTS = 5
MIN_FITNESS = 0.55
MUTATION_RATE = 0.12

INITIAL_CAPITAL = 100_000.0
TOTAL_CAPITAL = INITIAL_CAPITAL
GLOBAL_MAX_DRAWDOWN = -0.30     # -30% system stop
MAX_RISK_PER_TRADE = 0.15

AGENTS: Dict[int, Dict] = {}

# =========================
# MODELS
# =========================

class MarketInput(BaseModel):
    volatility: Optional[str] = "normal"
    regime: Optional[str] = "neutral"
    liquidity: Optional[str] = "normal"


class DecisionResult(BaseModel):
    generation: int
    agent_id: int
    agent_decision: str
    council_decision: str
    confidence: float
    pnl: float
    capital_after: float
    fitness: float
    genome: Dict
    votes: Dict
    note: str
    timestamp: float


# =========================
# AGENT CORE
# =========================

def create_genome():
    return {
        "risk": round(random.uniform(0.2, 0.8), 2),
        "patience": round(random.uniform(0.2, 0.8), 2),
        "aggression": round(random.uniform(0.2, 0.8), 2),
    }


def spawn_agent(agent_id: int):
    AGENTS[agent_id] = {
        "genome": create_genome(),
        "fitness": round(random.uniform(0.6, 0.8), 3),
        "capital": TOTAL_CAPITAL / MAX_AGENTS,
        "alive": True,
        "history": []
    }


for i in range(1, MAX_AGENTS + 1):
    spawn_agent(i)

# =========================
# CEO COUNCIL
# =========================

def ceo_optimist(decision, confidence):
    return decision if confidence > 0.6 else "HOLD"


def ceo_pessimist(decision, confidence):
    return decision if confidence > 0.75 else "HOLD"


def ceo_realist(decision, confidence):
    return decision if 0.55 <= confidence <= 0.8 else "HOLD"


def ceo_strategist(decision, confidence):
    if decision in ("BUY", "SELL") and confidence > 0.65:
        return decision
    return "HOLD"


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
    roll = random.random()
    if roll < genome["aggression"]:
        return "BUY"
    elif roll > 1 - genome["risk"]:
        return "SELL"
    return "HOLD"


def simulate_pnl(decision, confidence):
    if decision == "HOLD":
        return 0.0
    base = random.uniform(-0.04, 0.05)
    return round(base * confidence, 4)


def update_fitness(agent, pnl):
    delta = pnl * random.uniform(0.8, 1.2)
    agent["fitness"] = round(
        max(0.0, min(1.0, agent["fitness"] + delta)),
        3
    )
    agent["history"].append(agent["fitness"])
    if len(agent["history"]) > 30:
        agent["history"].pop(0)


def maybe_mutate(genome):
    if random.random() < MUTATION_RATE:
        k = random.choice(list(genome.keys()))
        genome[k] = round(
            max(0.1, min(0.9, genome[k] + random.uniform(-0.15, 0.15))),
            2
        )
        return f"mutation:{k}"
    return None


# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": 90,
        "agents_alive": sum(1 for a in AGENTS.values() if a["alive"]),
        "global_drawdown": round(global_drawdown(), 3),
        "ceo_council": list(CEO_COUNCIL.keys())
    }


@app.get("/health")
def health():
    return {"ok": True, "phase": 90}


# =========================
# SIMULATION
# =========================

@app.post("/simulate/market", response_model=DecisionResult)
def simulate_market(input: MarketInput):

    # GLOBAL KILL SWITCH
    if global_drawdown() <= GLOBAL_MAX_DRAWDOWN:
        return DecisionResult(
            generation=GENERATION,
            agent_id=-1,
            agent_decision="HALT",
            council_decision="HALT",
            confidence=0.0,
            pnl=0.0,
            capital_after=round(sum(a["capital"] for a in AGENTS.values()), 2),
            fitness=0.0,
            genome={},
            votes={},
            note="GLOBAL KILL SWITCH ACTIVATED",
            timestamp=time.time()
        )

    alive_agents = [i for i, a in AGENTS.items() if a["alive"]]
    agent_id = random.choice(alive_agents)
    agent = AGENTS[agent_id]

    genome = agent["genome"]

    decision = agent_decide(genome)
    confidence = round(random.uniform(0.5, 0.95), 2)

    # CEO COUNCIL
    votes = {name: ceo(decision, confidence) for name, ceo in CEO_COUNCIL.items()}
    final_decision = max(set(votes.values()), key=lambda d: list(votes.values()).count(d))

    pnl_pct = simulate_pnl(final_decision, confidence)
    pnl_value = agent["capital"] * pnl_pct
    agent["capital"] += pnl_value

    update_fitness(agent, pnl_pct)

    note = "stable"
    if agent["fitness"] < MIN_FITNESS:
        agent["alive"] = False
        spawn_agent(agent_id)
        note = "agent died → reborn"

    mutation_note = maybe_mutate(genome)
    if mutation_note:
        note += f" | {mutation_note}"

    return DecisionResult(
        generation=GENERATION,
        agent_id=agent_id,
        agent_decision=decision,
        council_decision=final_decision,
        confidence=confidence,
        pnl=round(pnl_value, 2),
        capital_after=round(agent["capital"], 2),
        fitness=agent["fitness"],
        genome=copy.deepcopy(genome),
        votes=votes,
        note=note,
        timestamp=time.time()
    )


# =========================
# DEBUG / CONTROL
# =========================

@app.get("/agents")
def agents():
    return AGENTS


@app.post("/reset")
def reset():
    AGENTS.clear()
    for i in range(1, MAX_AGENTS + 1):
        spawn_agent(i)
    return {"reset": True, "phase": 90}
