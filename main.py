from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import random
import time

app = FastAPI(title="ClawBot Phase 60 – Autonomous Core")

# =========================
# Models
# =========================

class MarketInput(BaseModel):
    risk_level: str
    volatility: str
    liquidity: str

class Agent(BaseModel):
    id: int
    strategy: str
    score: float = 0.0
    memory: List[Dict] = []

# =========================
# Global State
# =========================

AGENTS: List[Agent] = []
GENERATION = 0
LAST_TICK = time.time()

STRATEGIES = ["SCALP", "SWING", "TREND", "MEAN_REVERT"]

# =========================
# Helpers
# =========================

def init_agents(n: int = 5):
    global AGENTS
    AGENTS = [
        Agent(
            id=i,
            strategy=random.choice(STRATEGIES),
            score=0.0,
            memory=[]
        )
        for i in range(n)
    ]

def simulate_agent(agent: Agent, market: MarketInput) -> float:
    base = random.uniform(-1, 1)

    if market.volatility == "high":
        base *= 1.2
    if agent.strategy == "SCALP":
        base += 0.2

    return round(base, 4)

def compress_memory(agent: Agent):
    if len(agent.memory) > 5:
        agent.memory = agent.memory[-3:]

def autonomous_tick():
    global GENERATION, LAST_TICK
    now = time.time()

    if now - LAST_TICK < 5:
        return

    LAST_TICK = now
    GENERATION += 1

    # Evolution pressure
    for agent in AGENTS:
        agent.score *= 0.95  # decay

    # Cull worst agent
    if len(AGENTS) > 3:
        AGENTS.sort(key=lambda a: a.score)
        AGENTS.pop(0)

    # Spawn new agent
    new_id = max(a.id for a in AGENTS) + 1
    AGENTS.append(
        Agent(
            id=new_id,
            strategy=random.choice(STRATEGIES),
            score=0.0,
            memory=[]
        )
    )

# =========================
# Routes
# =========================

@app.on_event("startup")
def startup():
    init_agents()

@app.get("/")
def root():
    return {"status": "ClawBot Phase 60 running", "generation": GENERATION}

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    results = []

    for agent in AGENTS:
        pnl = simulate_agent(agent, data)
        agent.score += pnl
        agent.memory.append({
            "pnl": pnl,
            "t": time.time()
        })
        compress_memory(agent)

        results.append({
            "agent_id": agent.id,
            "strategy": agent.strategy,
            "pnl": pnl,
            "score": round(agent.score, 4)
        })

    autonomous_tick()

    return {
        "generation": GENERATION,
        "agents": results
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": GENERATION,
        "agents": [
            {
                "id": a.id,
                "strategy": a.strategy,
                "score": round(a.score, 4),
                "memory": a.memory
            }
            for a in AGENTS
        ]
    }
