# agents/ceo_alpha.py
# CEO Alpha — cautious, risk-first

def ceo_alpha(world_input: str, world_state: dict):
    """
    มองโลกในมุมระวังสูงสุด
    """
    risk = world_state.get("global_risk", "MEDIUM")

    if risk in ["HIGH", "LATENT_SYSTEMIC_RISK"]:
        stance = "DEFENSIVE"
        vote = "HIGH"
        reason = "Systemic risk still embedded in global structure"
    else:
        stance = "CAUTIOUS"
        vote = "MEDIUM"
        reason = "Risk not resolved, downside asymmetric"

    return {
        "ceo": "alpha",
        "global_risk": vote,
        "stance": stance,
        "confidence": 0.7,
        "reason": reason
    }
