# market/outcome_translator.py
"""
Phase 12.7
Translate real market conditions into Darwinism outcome
"""

from typing import Dict


def translate_market_to_outcome(market_state: Dict) -> Dict:
    """
    แปลง market_state -> outcome สำหรับ evolve_judgment / council
    """

    # -------------------------
    # Default outcome
    # -------------------------
    outcome = {
        "score": 0.0,          # -1 ถึง +1
        "global_risk": 0.5,    # 0 ถึง 1
        "confidence": 0.5,
        "tags": []
    }

    if not isinstance(market_state, dict):
        return outcome

    # -------------------------
    # Extract signals
    # -------------------------
    risk = market_state.get("risk_level", "medium")
    trend = market_state.get("trend", "sideways")
    volatility = market_state.get("volatility", "normal")
    liquidity = market_state.get("liquidity", "neutral")

    # -------------------------
    # Risk → global_risk
    # -------------------------
    if risk == "high":
        outcome["global_risk"] = 0.8
        outcome["tags"].append("RISK_HIGH")
    elif risk == "low":
        outcome["global_risk"] = 0.3
        outcome["tags"].append("RISK_LOW")

    # -------------------------
    # Trend → score
    # -------------------------
    if trend == "up":
        outcome["score"] += 0.4
        outcome["tags"].append("TREND_UP")
    elif trend == "down":
        outcome["score"] -= 0.4
        outcome["tags"].append("TREND_DOWN")

    # -------------------------
    # Volatility impact
    # -------------------------
    if volatility == "extreme":
        outcome["score"] -= 0.2
        outcome["global_risk"] += 0.1
        outcome["tags"].append("VOLATILITY_EXTREME")

    # -------------------------
    # Liquidity impact
    # -------------------------
    if liquidity == "tight":
        outcome["score"] -= 0.2
        outcome["tags"].append("LIQUIDITY_TIGHT")
    elif liquidity == "loose":
        outcome["score"] += 0.2
        outcome["tags"].append("LIQUIDITY_LOOSE")

    # -------------------------
    # Clamp values
    # -------------------------
    outcome["score"] = max(-1.0, min(1.0, outcome["score"]))
    outcome["global_risk"] = max(0.0, min(1.0, outcome["global_risk"]))

    # Confidence heuristic
    outcome["confidence"] = 1 - abs(outcome["score"]) * 0.5

    return outcome
