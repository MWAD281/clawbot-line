# agents/ceo_gamma.py
# CEO Gamma — Trend & Momentum

def ceo_gamma(user_input: str, world_state: dict):
    inertia = world_state.get("inertia", 1.0)

    if inertia > 2.0:
        return {
            "agent_id": "CEO_GAMMA",
            "faction": "TREND",
            "global_risk": "HIGH",
            "confidence": 0.65,
            "stance": "MOMENTUM_SHORT",
            "reason": "High inertia implies trend continuation and reflexivity"
        }

    return {
        "agent_id": "CEO_GAMMA",
        "faction": "TREND",
        "global_risk": "MEDIUM",
        "confidence": 0.6,
        "stance": "MOMENTUM_LONG",
        "reason": "No strong inertia; trend fragile"
    }
