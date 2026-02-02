# agents/ceo_gamma.py
# CEO Gamma — Tail Risk / Doom Scanner

def ceo_gamma(user_input: str, world_state: dict):
    """
    มองหาความเสี่ยงแบบหางซ้าย (rare but fatal)
    """

    global_risk = world_state.get("global_risk", "MEDIUM")
    inertia = world_state.get("inertia", 1.0)

    # ถ้าโลกดูนิ่ง แต่ inertia สูง → น่ากลัว
    if global_risk in ["LOW", "MEDIUM"] and inertia >= 1.5:
        return {
            "agent_id": "CEO_GAMMA",
            "global_risk": "HIGH",
            "confidence": 0.4,
            "stance": "ALERT",
            "reason": "Complacency with rising inertia increases tail risk"
        }

    # ถ้าโลกดูแย่อยู่แล้ว → Gamma จะไม่ตะโกน
    return {
        "agent_id": "CEO_GAMMA",
        "global_risk": global_risk,
        "confidence": 0.3,
        "stance": "OBSERVE",
        "reason": "Tail risk present but not accelerating"
    }
