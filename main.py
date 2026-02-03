import os
from typing import Optional, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ==================================================
# APP
# ==================================================

app = FastAPI(title="ClawBot Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# GLOBAL MEMORY (simple & stable)
# ==================================================

JUDGMENT_STATE = {
    "global_risk": "MEDIUM",
    "worldview": "defensive",
    "stance": "NEUTRAL",
    "confidence": 0.2,
    "inertia": 1.0,
    "source": "BOOT",
    "history": []
}


def get_judgment():
    return JUDGMENT_STATE


def overwrite_judgment(new_state: Dict):
    JUDGMENT_STATE.update(new_state)


# ==================================================
# COUNCIL (5 AGENTS)
# ==================================================

def council_vote(market: Dict) -> Dict:
    votes: List[str] = []

    # 1. Hawk – risk first
    if market["risk_level"] == "high":
        votes.append("RISK_UP")

    # 2. Dove – stabilization bias
    if market["trend"] == "down" and market["volatility"] != "extreme":
        votes.append("STABLE")

    # 3. Chaos – tail risk detector
    if market["volatility"] == "extreme":
        votes.append("CHAOS")

    # 4. Historian – crisis pattern
    if market["risk_level"] == "high" and market["trend"] == "down":
        votes.append("CRISIS_PATTERN")

    # 5. Survivor – liquidity stress
    if market["liquidity"] == "tight":
        votes.append("DEFENSIVE")

    return {
        "votes": votes,
        "count": len(votes)
    }


def apply_council(judgment: Dict, council: Dict) -> Dict:
    new_state = judgment.copy()

    # inertia: ไม่เปลี่ยนแรงเกิน
    inertia = judgment.get("inertia", 1.0)

    if "CHAOS" in council["votes"]:
        new_state["worldview"] = "fragile"
        new_state["confidence"] = min(1.0, judgment["confidence"] + 0.2 / inertia)

    if council["count"] >= 3:
        new_state["global_risk"] = "HIGH"
        new_state["stance"] = "DEFENSIVE"

    new_state["source"] = "COUNCIL"
    return new_state


# ==================================================
# MARKET FEEDBACK LOOP (simple deterministic)
# ==================================================

def run_market_feedback_loop(market: Dict) -> Dict:
    score = 0.0
    tags = []

    if market["risk_level"] == "high":
        score -= 0.3
        tags.append("RISK_HIGH")

    if market["trend"] == "down":
        score -= 0.3
        tags.append("TREND_DOWN")

    if market["volatility"] == "extreme":
        score -= 0.2
        tags.append("VOLATILITY_EXTREME")

    if market["liquidity"] == "tight":
        score -= 0.2
        tags.append("LIQUIDITY_TIGHT")

    return {
        "status": "FEEDBACK_APPLIED",
        "outcome": {
            "score": round(score, 2),
            "global_risk": abs(round(score, 2)),
            "confidence": min(1.0, abs(score)),
            "tags": tags
        }
    }


# ==================================================
# API
# ==================================================

@app.get("/")
def health():
    return {"status": "ClawBot alive"}


@app.get("/world")
def world_state():
    return get_judgment()


@app.post("/simulate/market")
def simulate_market(
    risk_level: Optional[str] = "high",
    trend: Optional[str] = "down",
    volatility: Optional[str] = "extreme",
    liquidity: Optional[str] = "tight"
):
    market_state = {
        "risk_level": risk_level,
        "trend": trend,
        "volatility": volatility,
        "liquidity": liquidity
    }

    # council deliberation
    council = council_vote(market_state)

    # feedback
    feedback = run_market_feedback_loop(market_state)

    # update judgment
    current = get_judgment()
    updated = apply_council(current, council)

    updated["history"].append({
        "source": "MARKET_FEEDBACK",
        "market_state": market_state,
        "outcome": feedback["outcome"]
    })

    overwrite_judgment(updated)

    return {
        "status": "SIMULATION_COMPLETE",
        "market_state": market_state,
        "council": council,
        "result": feedback,
        "judgment": updated
    }
