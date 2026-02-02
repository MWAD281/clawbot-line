# agents/ceo_alpha.py
# CEO Alpha — Crisis Hawk

def ceo_alpha(user_input: str, world_state: dict):
    risk = world_state.get("global_risk", "MEDIUM")

    if risk in ["HIGH", "LATENT_SYSTEMIC_RISK"]:
        return {
            "agent_id": "CEO_ALPHA",
            "faction": "RISK_OFF",
            "global_risk": vote,
            "stance": stance,
            "confidence": 0.7,
            "reason": reason
        }

    return {
        "agent_id": "CEO_ALPHA",
        "faction": "CRISIS",
        "global_risk": "MEDIUM",
        "confidence": 0.65,
        "stance": "CAUTIOUS",
        "reason": "Risk asymmetric despite surface stability"
    }
