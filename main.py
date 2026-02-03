from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import random
import time

app = FastAPI(title="ClawBot Phase 65 – Darwin Autonomous System")

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
    capital: float
    score: float = 0.0
    memory: List[Dict] = []

# =========================
# Global State
# =========================

AGENTS: List[Agent] = []
GENERATION = 0
LAST_TICK = time.time()

STRATEGIES = ["SCALP", "SWING", "TREND", "MEAN_REVERT"]
START_CAPITAL = 1000.0

# =========================
# Helpers
# =========================

def init_agents(n: int = 5):
    global AGENTS
    AGENTS = [
        Agent(
            id=i,
            strategy=random.choice(STRATEGIES),
            capital=START_CAPITAL,
            score=0.0,
            memory=[]
        )
        for i in range(n)
    ]

def position_size(agent: Agent, risk_level: str) -> float:
    risk_map = {
        "low": 0.01,
        "medium": 0.03,
        "high": 0.07
    }
    return agent.capital * risk_map.get(risk_level, 0.02)

def simulate_agent(agent: Agent, market: MarketInput) -> float:
    base = random.uniform(-1, 1)

    if market.volatility == "high":
        base *= 1.3
    if agent.strategy == "SCALP":
        base += 0.2
    if agent.strategy == "MEAN_REVERT":
        base *= 0.8

    return round(base, 4)

def compress_memory(agent: Agent):
    if len(agent.memory) > 6:
        agent.memory = agent.memory[-3:]

def rebirth_agent(dead_agent: Agent) -> Agent:
    return Agent(
        id=dead_agent.id,
        strategy=random.choice(STRATEGIES),
        capital=START_CAPITAL,
        score=0.0,
        memory=[]
    )

def autonomous_tick():
    global GENERATION, LAST_TICK, AGENTS

    now = time.time()
    if now - LAST_TICK < 5:
        return

    LAST_TICK = now
    GENERATION += 1

    survivors = []

    for agent in AGENTS:
        if agent.capital <= 0:
            survivors.append(rebirth_agent(agent))
        else:
            agent.score *= 0.97
            survivors.append(agent)

    # Cull worst if overcrowded
    if len(survivors) > 6:
        survivors.sort(key=lambda a: a.capital)
        survivors = survivors[-5:]

    AGENTS = survivors

# =========================
# Routes
# =========================

@app.on_event("startup")
def startup():
    init_agents()

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 65 running",
        "generation": GENERATION,
        "agents": len(AGENTS)
    }

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    results = []

    for agent in AGENTS:
        size = position_size(agent, data.risk_level)
        pnl_ratio = simulate_agent(agent, data)
        pnl = round(size * pnl_ratio, 2)

        agent.capital += pnl
        agent.score += pnl_ratio

        agent.memory.append({
            "pnl": pnl,
            "capital": round(agent.capital, 2),
            "t": time.time()
        })

        compress_memory(agent)

        results.append({
            "agent_id": agent.id,
            "strategy": agent.strategy,
            "pnl": pnl,
            "capital": round(agent.capital, 2),
            "score": round(agent.score, 3)
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
                "capital": round(a.capital, 2),
                "score": round(a.score, 3),
                "memory": a.memory
            }
            for a in AGENTS
        ]
    }
