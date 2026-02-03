# agents/ceo_council.py

from agents.ceo_profile import CEO_PROFILES
from agents.ceo_debate import ceo_debate
from memory.judgment_state import get_judgment


def run_ceo_council(ai_text: str):
    judgment = get_judgment()
    regime = judgment.get("regime", "NEUTRAL")

    opinions = []

    for name, profile in CEO_PROFILES.items():
        result = ceo_debate(ai_text, name, profile)

        # regime advantage
        if profile.get("preferred_regime") == regime:
            result["market_score"] = result["score"] * 1.2
        else:
            result["market_score"] = result["score"]

        result["regime"] = regime
        opinions.append(result)

    return opinions


def adjust_ceo_fitness(opinions: list):
    for o in opinions:
        if o["market_score"] > 0:
            CEO_PROFILES[o["ceo"]]["weight"] *= 1.05
        else:
            CEO_PROFILES[o["ceo"]]["weight"] *= 0.97
