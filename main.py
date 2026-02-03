from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
import time
import copy

app = FastAPI(
    title="ClawBot Phase 80 – Darwin Core",
    version="80.0.0",
    description="Selection, death, rebirth, mutation, tournament"
)

# =========================
# GLOBAL STATE (IN-MEMORY)
# =========================

AGENTS: Dict[int, Dict] = {}
GENERATION = 80
MAX_AGENTS = 5
MIN_FITNESS = 0.55
MUTATION_RATE = 0.15

# =========================
# MODELS
# =========================

class MarketInput(BaseModel):
    volatility: Optional[str] = "normal"
    regime: Optional[str] = "neutral"
    liquidity: Optional[str] = "normal"


class SimulationResult(BaseModel):
    generation: int
    agent_id: int
    decision: str
    confidence: float
    fitness: float
    genome: Dict
    note: str
    timestamp: float


# =========================
# INIT
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
        "history": [],
        "alive": True
    }


for i in range(1, MAX_AGENTS + 1):
    spawn_agent(i)

# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": 80,
        "agents_alive": sum(1 for a in AGENTS.values() if a["alive"]),
        "darwinism": True
    }


@app.get("/health")
def health():
    return {"ok": True}


# =========================
# CORE SIMULATION
# =========================

@app.post("/simulate/market", response_model=SimulationResult)
def simulate_market(input: MarketInput):
    alive_agents = [i for i, a in AGENTS.items() if a["alive"]]
    agent_id = random.choice(alive_agents)
    agent = AGENTS[agent_id]

    genome = agent["genome"]

    # Decision logic (genome-influenced)
    roll = random.random()
    if roll < genome["aggression"]:
        decision = "BUY"
    elif roll > 1 - genome["risk"]:
        decision = "SELL"
    else:
        decision = "HOLD"

    confidence = round(random.uniform(0.5, 0.95), 2)

    # Fitness update
    delta = (confidence - 0.5) * random.uniform(0.8, 1.2)
    agent["fitness"] = round(
        max(0.0, min(1.0, agent["fitness"] + delta * 0.1)),
        3
    )

    agent["history"].append(agent["fitness"])
    if len(agent["history"]) > 30:
        agent["history"].pop(0)

    note = "Stable"

    # =========================
    # Phase 77–78: Selection & Death
    # =========================

    if agent["fitness"] < MIN_FITNESS:
        agent["alive"] = False
        note = "Agent died (low fitness)"

        # Rebirth
        dead_id = agent_id
        spawn_agent(dead_id)
        note += " → reborn with new genome"

    # =========================
    # Phase 79: Mutation
    # =========================

    if random.random() < MUTATION_RATE:
        trait = random.choice(list(genome.keys()))
        genome[trait] = round(
            max(0.1, min(0.9, genome[trait] + random.uniform(-0.15, 0.15))),
            2
        )
        note += f" | mutation on {trait}"

    return SimulationResult(
        generation=GENERATION,
        agent_id=agent_id,
        decision=decision,
        confidence=confidence,
        fitness=agent["fitness"],
        genome=copy.deepcopy(genome),
        note=note,
        timestamp=time.time()
    )


# =========================
# TOURNAMENT (PHASE 80)
# =========================

@app.get("/tournament")
def tournament():
    ranked = sorted(
        AGENTS.items(),
        key=lambda x: x[1]["fitness"],
        reverse=True
    )

    winner_id, winner = ranked[0]

    return {
        "winner": winner_id,
        "fitness": winner["fitness"],
        "genome": winner["genome"],
        "ranking": [
            {"agent": i, "fitness": a["fitness"], "alive": a["alive"]}
            for i, a in ranked
        ]
    }


# =========================
# DEBUG / RESET
# =========================

@app.get("/agents")
def agents():
    return AGENTS


@app.post("/reset")
def reset():
    AGENTS.clear()
    for i in range(1, MAX_AGENTS + 1):
        spawn_agent(i)
    return {"reset": True}
