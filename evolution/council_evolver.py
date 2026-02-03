# evolution/council_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment
from agents.ceo_council import run_ceo_council, adjust_ceo_fitness
from evolution.strategy_learner import learn_from_judgment
from evolution.regime_detector import update_regime


def evolve_from_council(ai_text: str) -> dict:
    opinions = run_ceo_council(ai_text)
    judgment = get_judgment()

    if not opinions:
        return judgment

    total_weight = sum(o["weight"] for o in opinions)
    avg_score = sum(o["market_score"] * o["weight"] for o in opinions) / total_weight
    avg_risk = sum(o["global_risk"] * o["weight"] for o in opinions) / total_weight

    judgment.setdefault("confidence", 0.5)
    judgment["global_risk"] = round(avg_risk, 3)

    if avg_score < -0.3 or avg_risk > 0.65:
        judgment.update({
            "worldview": "defensive",
            "stance": "RISK_OFF",
            "confidence": max(0.1, judgment["confidence"] - 0.1)
        })

    elif avg_score > 0.3 and avg_risk < 0.45:
        judgment.update({
            "worldview": "aggressive",
            "stance": "RISK_ON",
            "confidence": min(0.9, judgment["confidence"] + 0.1)
        })

    else:
        judgment.update({
            "worldview": "neutral",
            "stance": "WAIT"
        })

    # 🔥 NEW: regime detection
    update_regime(judgment)

    overwrite_judgment(judgment)

    # 🧠 learn
    learn_from_judgment(judgment)

    # 🧬 Darwinism
    adjust_ceo_fitness(opinions)

    return judgment
