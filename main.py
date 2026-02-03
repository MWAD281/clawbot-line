from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import random
import uuid
import copy

app = FastAPI(
    title="ClawBot Phase 38 – Mutation Engine",
    version="0.4.0"
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Models
# =========================
class MarketInput(BaseModel):
    risk_level: str
    trend: str
    volatility: str
    liquidity: str

# =========================
# Agent Registry
# =========================
AGENTS: Dict[str, dict] = {}

def random_gene():
    return {
        "aggression": round(random.uniform(0.0, 1.0), 2),
        "risk_tolerance": round(random.uniform(0.0, 1.0), 2),
        "reactivity": round(random.uniform(0.0, 1.0), 2),
    }

def mutate_gene(parent_gene):
    gene = copy.deepcopy(parent_gene)
    key = random.choice(list(gene.keys()))
    gene[key] = min(1.0, max(0.0, gene[key] + random.uniform(-0.15, 0.15)))
    return gene

def spawn_agent(parent=None):
    agent_id = str(uuid.uuid4())[:8]
    AGENTS[agent_id] = {
        "id": agent_id,
        "score": 0.0,
        "alive": True,
        "gene": mutate_gene(parent["gene"]) if parent else random_gene(),
        "created_at": datetime.utcnow().isoformat()
    }

# initial population
for _ in range(3):
    spawn_agent()

# =========================
# Memory
# =========================
MEMORY: List[dict] = []

# =========================
# Decision Engine
# =========================
def agent_decision(agent, data: MarketInput):
    g = agent["gene"]

    aggression = g["aggression"]
    risk = g["risk_tolerance"]

    danger = 1 if data.risk_level == "high" else 0
    trend_up = 1 if data.trend == "up" else -1 if data.trend == "down" else 0

    score = aggression * trend_up - danger * (1 - risk)

    if score > 0.3:
        return "AGGRESSIVE"
    if score < -0.3:
        return "DEFENSIVE"
    return "HOLD"

# =========================
# Scoring
# =========================
def evaluate(decision: str, data: MarketInput):
    if decision == "AGGRESSIVE" and data.trend == "up":
        return +1.2
    if decision == "DEFENSIVE" and data.trend == "down":
        return +1.0
    if decision == "AGGRESSIVE" and data.trend == "down":
        return -1.5
    return -0.1

# =========================
# Darwinism + Mutation
# =========================
def evolution_cycle():
    global AGENTS

    # sort by performance
    ranked = sorted(AGENTS.values(), key=lambda x: x["score"], reverse=True)

    survivors = ranked[:max(1, len(ranked)//2)]
    dead = ranked[len(survivors):]

    for d in dead:
        AGENTS.pop(d["id"], None)

    # reproduce from best agents
    while len(AGENTS) < 3:
        parent = random.choice(survivors)
        spawn_agent(parent)

# =========================
# Root
# =========================
@app.get("/")
def root():
    return {
        "status": "ClawBot Phase 38 ONLINE",
        "agents": len(AGENTS),
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# Simulation
# =========================
@app.post("/simulate/market")
def simulate_market(data: MarketInput):
    cycle = []

    for agent in AGENTS.values():
        decision = agent_decision(agent, data)
        reward = evaluate(decision, data)
        agent["score"] += reward

        cycle.append({
            "agent_id": agent["id"],
            "decision": decision,
            "reward": reward,
            "score": agent["score"],
            "gene": agent["gene"]
        })

    evolution_cycle()

    MEMORY.append({
        "input": data.dict(),
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "engine": "ClawBot Phase 38",
        "cycle": cycle,
        "agents_alive": len(AGENTS)
    }

# =========================
# Dashboard
# =========================
@app.get("/dashboard")
def dashboard():
    return {
        "phase": 38,
        "agents": list(AGENTS.values()),
        "memory_size": len(MEMORY),
        "status": "MUTATING",
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================
# LINE Webhook
# =========================
@app.post("/line/webhook")
async def line_webhook(request: Request):
    return {"ok": True}
