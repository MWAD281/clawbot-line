from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import uuid


# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Darwinism Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# GLOBAL JUDGMENT MEMORY
# ==================================================

JUDGMENT_STATE = {
    "global_risk": "MEDIUM",
    "worldview": "defensive",
    "stance": "NEUTRAL",
    "confidence": 0.3,
    "inertia": 1.2,
    "generation": 1,
    "history": []
}


# ==================================================
# DARWIN COUNCIL
# ==================================================

def new_agent(name: str) -> Dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "hp": 100,
        "fitness": 1.0,
        "alive": True
    }


COUNCIL: List[Dict] = [
    new_agent("HAWK"),
    new_agent("DOVE"),
    new_agent("CHAOS"),
    new_agent("HISTORIAN"),
    new_agent("SURVIVOR")
]


# ==================================================
# AGENT BEHAVIOR
# ==================================================

def agent_vote(agent: Dict, market: Dict) -> str | None:
    if not agent["alive"]:
        return None

    name = agent["name"]

    if name == "HAWK" and market["risk_level"] == "high":
        return "RISK_UP"

    if name == "DOVE" and market["trend"] == "down":
        return "STABLE"

    if name == "CHAOS" and market["volatility"] == "extreme":
        return "CHAOS"

    if name == "HISTORIAN" and market["risk_level"] == "high":
        return "CRISIS_PATTERN"

    if name == "SURVIVOR" and market["liquidity"] == "tight":
        return "DEFENSIVE"

    return None


def council_deliberate(market: Dict) -> Dict:
    votes = []
    contributors = []

    for agent in COUNCIL:
        vote = agent_vote(agent, market)
        if vote:
            weighted = agent["fitness"]
            votes.append((vote, weighted))
            contributors.append(agent)

    return {
        "votes": votes,
        "contributors": contributors
    }


# ==================================================
# FEEDBACK & FITNESS
# ==================================================

def evaluate_market(market: Dict) -> Dict:
    score = 0.0

    if market["risk_level"] == "high":
        score -= 0.3
    if market["trend"] == "down":
        score -= 0.3
    if market["volatility"] == "extreme":
        score -= 0.2
    if market["liquidity"] == "tight":
        score -= 0.2

    return {
        "score": round(score, 2),
        "severity": abs(score)
    }


def apply_darwinism(result: Dict, contributors: List[Dict]):
    severity = result["severity"]

    for agent in contributors:
        if severity > 0.6:
            agent["hp"] -= int(severity * 40)
            agent["fitness"] *= 0.9
        else:
            agent["fitness"] *= 1.05

        if agent["hp"] <= 0:
            agent["alive"] = False


def rebirth():
    global COUNCIL

    dead = [a for a in COUNCIL if not a["alive"]]
    for agent in dead:
        COUNCIL.remove(agent)
        mutant = new_agent(agent["name"] + "_v2")
        mutant["fitness"] = round(random.uniform(0.8, 1.2), 2)
        COUNCIL.append(mutant)


# ==================================================
# JUDGMENT UPDATE
# ==================================================

def update_judgment(votes: List, result: Dict):
    global JUDGMENT_STATE

    if result["severity"] > 0.7:
        JUDGMENT_STATE["global_risk"] = "HIGH"
        JUDGMENT_STATE["stance"] = "DEFENSIVE"
        JUDGMENT_STATE["worldview"] = "fragile"

    JUDGMENT_STATE["confidence"] = min(
        1.0,
        JUDGMENT_STATE["confidence"] + (0.1 if result["severity"] < 0.6 else -0.1)
    )

    JUDGMENT_STATE["generation"] += 1


# ==================================================
# API
# ==================================================

@app.get("/")
def health():
    return {"status": "ClawBot Darwinism Alive"}


@app.get("/council")
def council_state():
    return COUNCIL


@app.get("/world")
def world():
    return JUDGMENT_STATE


@app.post("/simulate/market")
def simulate_market(
    risk_level: str = "high",
    trend: str = "down",
    volatility: str = "extreme",
    liquidity: str = "tight"
):
    market = {
        "risk_level": risk_level,
        "trend": trend,
        "volatility": volatility,
        "liquidity": liquidity
    }

    council_result = council_deliberate(market)
    evaluation = evaluate_market(market)

    apply_darwinism(evaluation, council_result["contributors"])
    rebirth()
    update_judgment(council_result["votes"], evaluation)

    JUDGMENT_STATE["history"].append({
        "market": market,
        "evaluation": evaluation,
        "votes": council_result["votes"]
    })

    return {
        "status": "SIMULATION_COMPLETE",
        "market": market,
        "evaluation": evaluation,
        "council_votes": council_result["votes"],
        "council_state": COUNCIL,
        "judgment": JUDGMENT_STATE
    }
