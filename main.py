from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, List
import random
import time

app = FastAPI(
    title="ClawBot Phase 75 – Cognitive Evolution Core",
    version="75.0.0",
    description="Self-reflection, memory, fitness & evolution signals"
)

# =========================
# In-Memory State (SAFE)
# =========================

AGENT_MEMORY: Dict[int, List[Dict]] = {}
AGENT_FITNESS: Dict[int, float] = {}
AGENT_CONFIDENCE_HISTORY: Dict[int, List[float]] = {}

# =========================
# Data Models
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
    reflection: str
    timestamp: float


# =========================
# Root
# =========================

@app.get("/")
def root():
    return {
        "status": "ClawBot online",
        "phase": 75,
        "features": [
            "self_reflection",
            "memory",
            "fitness_tracking",
            "evolution_signal"
        ],
        "ready": True
    }


# =========================
# Health Check
# =========================

@app.get("/health")
def health():
    return {"ok": True}


# =========================
# Core Simulation
# =========================

@app.post("/simulate/market", response_model=SimulationResult)
def simulate_market(input: MarketInput):
    agent_id = random.randint(1, 5)
    decision = random.choice(["BUY", "SELL", "HOLD"])
    confidence = round(random.uniform(0.5, 0.95), 2)

    # ---- Phase 72: Confidence Drift ----
    history = AGENT_CONFIDENCE_HISTORY.setdefault(agent_id, [])
    history.append(confidence)
    if len(history) > 20:
        history.pop(0)

    avg_conf = sum(history) / len(history)

    # ---- Phase 74: Fitness Score ----
    fitness = round(avg_conf * random.uniform(0.9, 1.1), 3)
    AGENT_FITNESS[agent_id] = fitness

    # ---- Phase 71: Self Reflection ----
    if confidence > avg_conf:
        reflection = "Confidence improving"
    elif confidence < avg_conf:
        reflection = "Confidence declining"
    else:
        reflection = "Confidence stable"

    # ---- Phase 73: Memory ----
    memory = AGENT_MEMORY.setdefault(agent_id, [])
    memory.append({
        "decision": decision,
        "confidence": confidence,
        "fitness": fitness,
        "timestamp": time.time()
    })
    if len(memory) > 50:
        memory.pop(0)

    # ---- Phase 75: Evolution Signal (soft) ----
    if fitness < 0.55:
        reflection += " | Evolution signal: WEAK"
    elif fitness > 0.8:
        reflection += " | Evolution signal: STRONG"

    return SimulationResult(
        generation=75,
        agent_id=agent_id,
        decision=decision,
        confidence=confidence,
        fitness=fitness,
        reflection=reflection,
        timestamp=time.time()
    )


# =========================
# Debug / Introspection
# =========================

@app.get("/agents")
def agents_state():
    return {
        "agents": {
            agent_id: {
                "fitness": AGENT_FITNESS.get(agent_id),
                "memory_size": len(AGENT_MEMORY.get(agent_id, [])),
                "confidence_samples": len(AGENT_CONFIDENCE_HISTORY.get(agent_id, []))
            }
            for agent_id in range(1, 6)
        }
    }


@app.post("/reset")
def reset_memory():
    AGENT_MEMORY.clear()
    AGENT_FITNESS.clear()
    AGENT_CONFIDENCE_HISTORY.clear()
    return {"reset": True}
