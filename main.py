from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import random
import time
import statistics

app = FastAPI(title="ClawBot Phase 70 – Self Improving Darwin AI")

# =========================
# Models
# =========================

class MarketInput(BaseModel):
    risk_level: str
    volatility: str
    liquidity: str

class Genome(BaseModel):
    aggression: float
    risk_tolerance: float
    adaptability: float

class Agent(BaseModel):
    id: int
    strategy: str
    capital: float
    genome: Genome
    trades: int = 0
    wins: int = 0
    total_pnl: float = 0.0
    memory: List[Dict] = []

# =========================
# Global State
# =========================

AGENTS: List[Agent] = []
GENERATION = 0
LAST_TICK = time.time()

STRATEGIES = ["SCALP", "SWING", "TREND", "MEAN_REVERT"]
START_CAPITAL = 1000.0
POPULATION = 6

# =========================
# Helpers
# =========================

def random_genome():
    return Genome(
        aggression=round(random.uniform(0.3, 1.0), 2),
        risk_tolerance=round(random.uniform(0.3, 1.0), 2),
        adaptability=round(random.uniform(0.3, 1.0), 2),
    )

def init_agents():
    global AGENTS
    AGENTS = [
        Agent(
            id=i,
            strategy=random.choice(STRATEGIES),
            capital=START_CAPITAL,
            genome=random_genome(),
        )
        for i in range(POPULATION)
    ]

def position_size(agent: Agent):
    return agent.capital * 0.02 * agent.genome.risk_tolerance

def simulate_trade(agent: Agent, market: MarketInput):
    bias = agent.genome.aggression - 0.5
    noise = random.uniform(-1, 1)

    if market.volatility == "high":
        noise *= 1.3

    pnl_ratio = noise + bias
    pnl = round(position_size(agent) * pnl_ratio, 2)

    agent.capital += pnl
    agent.total_pnl += pnl
    agent.trades += 1

    if pnl > 0:
        agent.wins += 1

    agent.memory.append({
        "pnl": pnl,
        "capital": round(agent.capital, 2),
        "t": time.time()
    })

    if len(agent.memory) > 6:
        agent.memory = agent.memory[-3:]

def fitness(agent: Agent):
    if agent.trades == 0:
        return 0
    win_rate = agent.wins / agent.trades
    avg_pnl = agent.total_pnl / agent.trades
    return round(win_rate * 0.6 + avg_pnl * 0.4, 4)

def mutate(genome: Genome):
    return Genome(
        aggression=min(max(genome.aggression + random.uniform(-0.1, 0.1), 0.1), 1),
        risk_tolerance=min(max(genome.risk_tolerance + random.uniform(-0.1, 0.1), 0.1), 1),
        adaptability=min(max(genome.adaptability + random.uniform(-0.1, 0.1), 0.1), 1),
    )

def evolve():
    global AGENTS, GENERATION
    GENERATION += 1

    scored = sorted(AGENTS, key=fitness, reverse=True)
    elites = scored[:2]

    new_agents = []
    for i in range(POPULATION):
        parent = random.choice(elites)
        new_agents.append(
            Agent(
                id=i,
                strategy=parent.strategy,
                capital=START_CAPITAL,
                genome=mutate(parent.genome)
            )
        )

    AGENTS = new_agents

# =========================
# Routes
# =========================

@app.on_event("startup")
def startup():
    init_agents()

@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 70 ACTIVE",
        "generation": GENERATION,
        "population": len(AGENTS)
    }

@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    for agent in AGENTS:
        simulate_trade(agent, data)

    if all(a.trades >= 5 for a in AGENTS):
        evolve()

    return {
        "generation": GENERATION,
        "agents": [
            {
                "id": a.id,
                "capital": round(a.capital, 2),
                "fitness": fitness(a),
                "genome": a.genome
            }
            for a in AGENTS
        ]
    }

@app.get("/dashboard")
def dashboard():
    return {
        "generation": GENERATION,
        "agents": [
            {
                "id": a.id,
                "capital": round(a.capital, 2),
                "trades": a.trades,
                "wins": a.wins,
                "fitness": fitness(a),
                "genome": a.genome,
                "memory": a.memory
            }
            for a in AGENTS
        ]
    }
