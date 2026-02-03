# agents/ceo_debate.py

from memory.strategy_memory import get_strategy_bias
import random


def ceo_debate(ai_text: str, ceo_name: str, profile: dict) -> dict:
    bias = profile["bias"]

    base_score = random.uniform(-1, 1)
    risk = random.uniform(0.2, 0.8)

    stance = "WAIT"
    if base_score > 0.3:
        stance = "RISK_ON"
    elif base_score < -0.3:
        stance = "RISK_OFF"

    # memory influence
    regime = profile.get("last_regime", "NEUTRAL")
    memory_bias = get_strategy_bias(stance, regime)

    final_score = base_score + memory_bias * 0.5

    return {
        "ceo": ceo_name,
        "stance": stance,
        "score": final_score,
        "global_risk": risk,
        "weight": profile["weight"]
    }
