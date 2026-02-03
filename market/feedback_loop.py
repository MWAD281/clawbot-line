# market/feedback_loop.py

from typing import Dict

from memory.judgment_state import get_judgment, overwrite_judgment
from memory.judgment_drift import apply_judgment_drift


# =========================
# MARKET SCORING
# =========================

def score_market_state(market_state: Dict) -> Dict:
    score = 0.0
    tags = []

    if market_state.get("risk_level") == "high":
        score -= 0.3
        tags.append("RISK_HIGH")

    if market_state.get("trend") == "down":
        score -= 0.2
        tags.append("TREND_DOWN")

    if market_state.get("volatility") == "extreme":
        score -= 0.2
        tags.append("VOLATILITY_EXTREME")

    if market_state.get("liquidity") == "tight":
        score -= 0.1
        tags.append("LIQUIDITY_TIGHT")

    global_risk = min(1.0, abs(score) + 0.1)
    confidence = min(1.0, 0.4 + abs(score))

    return {
        "score": round(score, 2),
        "global_risk": round(global_risk, 2),
        "confidence": round(confidence, 2),
        "tags": tags
    }


# =========================
# FEEDBACK LOOP
# =========================

def run_market_feedback_loop(market_state: Dict) -> Dict:
    """
    Main market → judgment evolution loop
    """

    outcome = score_market_state(market_state)

    current_judgment = get_judgment()

    # Apply drift (slow evolution)
    new_judgment = apply_judgment_drift(
        current=current_judgment,
        incoming_risk_score=outcome["global_risk"],
        confidence=outcome["confidence"]
    )

    # Append history safely
    history = current_judgment.get("history", [])
    history.append({
        "source": "MARKET_FEEDBACK",
        "market_state": market_state,
        "outcome": outcome
    })

    new_judgment["history"] = history[-20:]  # cap memory

    overwrite_judgment(new_judgment)

    return {
        "status": "FEEDBACK_APPLIED",
        "outcome": outcome,
        "judgment": {
            "global_risk": new_judgment.get("global_risk"),
            "worldview": new_judgment.get("worldview"),
            "stance": new_judgment.get("stance"),
            "inertia": new_judgment.get("inertia"),
            "confidence": outcome.get("confidence")
        }
    }
