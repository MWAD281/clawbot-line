# agents/ceo_feedback.py

def score_ceo_against_market(ceo_opinion: dict, market: dict) -> float:
    """
    ถ้า CEO stance ตรงกับ regime → reward
    ถ้าผิด → penalty
    """

    score = ceo_opinion["score"]
    risk = ceo_opinion["global_risk"]

    if market["regime"] == "RISK_ON":
        return score + market["reward_bias"] - risk * 0.2

    if market["regime"] == "RISK_OFF":
        return score - market["penalty_bias"] - risk * 0.3

    return score * 0.5
