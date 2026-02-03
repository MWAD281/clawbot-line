from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
import time
import copy

app = FastAPI(
    title="ClawBot Phase 90 – CEO Council",
    version="90.0.0",
    description="Multi-CEO voting, capital allocation, risk guard"
)

# =========================
# GLOBAL STATE
# =========================

GENERATION = 90
AGENTS: Dict[int, Dict] = {}
MAX_AGENTS = 5
MIN_FITNESS = 0.55
MUTATION_RATE = 0.12

TOTAL_CAPITAL = 100_000
MAX_RISK_PER_TRADE = 0.15

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
    capital_allocated: float
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
    return "HOLD" if confidence < 0.75 else decision


def ceo_realist(decision, confidence):
    return decision if 0.55 <= confidence <= 0.8 else "HOLD"


def ceo_strategist(decision, confidence):
    if decision == "BUY" and confidence > 0.65:
        return "BUY"
    if decision == "SELL" and confidence > 0.65:
        return "SELL"
    return "HOLD"


CEO_COUNCIL = {
    "optimist": ceo_optimist,
    "pessimist": ceo_pessimist,
    "realist": ceo_realist,
    "strategist": ceo_strategist,
}

# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": 90,
        "agents_alive": sum(1 for a in AGENTS.values() if a["alive"]),
        "ceo_council": list(CEO_COUNCIL.keys())
    }


@app.get("/health")
def health():
    return {"ok": True}


# =========================
# CORE LOGIC
# =========================

def agent_decide(genome):
    roll = random.random()
    if roll < genome["aggression"]:
        return "BUY"
    elif roll > 1 - genome["risk"]:
        return "SELL"
    return "HOLD"


def update_fitness(agent, confidence):
    delta = (confidence - 0.5) * random.uniform(0.8, 1.2)
    agent["fitness"] = round(
        max(0.0, min(1.0, agent["fitness"] + delta * 0.1)),
        3
    )
    agent["history"].append(agent["fitness"])
    if len(agent["history"]) > 25:
        agent["history"].pop(0)


def maybe_mutate(genome):
    if random.random() < MUTATION_RATE:
        k = random.choice(list(genome.keys()))
        genome[k] = round(
            max(0.1, min(0.9, genome[k] + random.uniform(-0.15, 0.15))),
            2
        )
        return f"mutation on {k}"
    return None


def capital_allocation(decision, confidence):
    if decision == "HOLD":
        return 0.0
    risk_factor = min(confidence, MAX_RISK_PER_TRADE)
    return round(TOTAL_CAPITAL * risk_factor, 2)


# =========================
# SIMULATION ENDPOINT
# =========================

@app.post("/simulate/market", response_model=DecisionResult)
def simulate_market(input: MarketInput):
    alive_agents = [i for i, a in AGENTS.items() if a["alive"]]
    agent_id = random.choice(alive_agents)
    agent = AGENTS[agent_id]

    genome = agent["genome"]

    decision = agent_decide(genome)
    confidence = round(random.uniform(0.5, 0.95), 2)

    update_fitness(agent, confidence)

    # Death & Rebirth
    note = "stable"
    if agent["fitness"] < MIN_FITNESS:
        agent["alive"] = False
        spawn_agent(agent_id)
        note = "agent died → reborn"

    mutation_note = maybe_mutate(genome)
    if mutation_note:
        note += f" | {mutation_note}"

    # =========================
    # CEO COUNCIL VOTE
    # =========================

    votes = {}
    for name, ceo in CEO_COUNCIL.items():
        votes[name] = ceo(decision, confidence)

    final_decision = max(
        set(votes.values()),
        key=lambda d: list(votes.values()).count(d)
    )

    capital = capital_allocation(final_decision, confidence)

    return DecisionResult(
        generation=GENERATION,
        agent_id=agent_id,
        agent_decision=decision,
        council_decision=final_decision,
        capital_allocated=capital,
        fitness=agent["fitness"],
        genome=copy.deepcopy(genome),
        votes=votes,
        note=note,
        timestamp=time.time()
    )


# =========================
# DASHBOARD / DEBUG
# =========================

@app.get("/agents")
def agents():
    return AGENTS


@app.get("/council")
def council():
    return list(CEO_COUNCIL.keys())


@app.post("/reset")
def reset():
    AGENTS.clear()
    for i in range(1, MAX_AGENTS + 1):
        spawn_agent(i)
    return {"reset": True}
