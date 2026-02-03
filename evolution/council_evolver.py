# evolution/council_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment
from agents.ceo_council import run_ceo_council


def evolve_from_council(ai_raw: dict) -> dict:
    """
    รวมเสียง CEO → evolve worldview กลาง
    """
    opinions = run_ceo_council(ai_raw)

    total_weight = sum(o["weight"] for o in opinions)
    avg_score = sum(o["score"] * o["weight"] for o in opinions) / total_weight
    avg_risk = sum(o["global_risk"] * o["weight"] for o in opinions) / total_weight

    judgment = get_judgment()

    # default safe
    judgment.setdefault("worldview", "neutral")
    judgment.setdefault("confidence", 0.5)

    if avg_score < -0.4 or avg_risk > 0.7:
        judgment["worldview"] = "defensive"
        judgment["stance"] = "RISK_OFF"
        judgment["confidence"] = max(0.1, judgment["confidence"] - 0.1)

    elif avg_score > 0.4 and avg_risk < 0.4:
        judgment["worldview"] = "aggressive"
        judgment["stance"] = "RISK_ON"
        judgment["confidence"] = min(0.9, judgment["confidence"] + 0.1)

    else:
        judgment["worldview"] = "neutral"
        judgment["stance"] = "WAIT_AND_SEE"

    overwrite_judgment(judgment)
    return judgment
