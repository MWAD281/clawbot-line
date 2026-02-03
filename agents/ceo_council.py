# agents/ceo_council.py

from agents.ceo_genome import spawn_ceo, should_die
from agents.ceo_debate import ceo_debate
import uuid

CEO_PROFILES = {
    "Defensive_CEO": {
        "bias": "risk_downside",
        "weight": 1.0,
        "alive": True,
        "memory": []
    },
    "Aggressive_CEO": {
        "bias": "growth_upside",
        "weight": 1.0,
        "alive": True,
        "memory": []
    },
    "Systemic_CEO": {
        "bias": "systemic_risk",
        "weight": 1.2,
        "alive": True,
        "memory": []
    }
}


def run_ceo_council(ai_text: str):
    """
    CEO Debate → Vote
    """
    results = []

    for name, profile in CEO_PROFILES.items():
        if not profile["alive"]:
            continue

        result = ceo_debate(ai_text, name, profile)

        # memory
        profile["memory"].append(result)
        if len(profile["memory"]) > 50:
            profile["memory"] = profile["memory"][-50:]

        results.append(result)

    return results


def adjust_ceo_fitness(results: list):
    dead = []

    for r in results:
        ceo = CEO_PROFILES.get(r["ceo"])
        if not ceo:
            continue

        ceo["weight"] += r["score"] * 0.1
        ceo["weight"] = max(0.05, min(2.0, ceo["weight"]))

        if should_die(ceo):
            ceo["alive"] = False
            dead.append(r["ceo"])

    # ♻️ Rebirth
    for name in dead:
        parent = CEO_PROFILES.get(name)
        if not parent:
            continue

        new_name = f"CEO_{uuid.uuid4().hex[:6]}"
        CEO_PROFILES[new_name] = spawn_ceo(name, parent)
