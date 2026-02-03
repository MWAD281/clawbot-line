# agents/ceo_council.py

from agents.ceo_genome import spawn_ceo, should_die
from agents.ceo_debate import ceo_debate
from agents.ceo_feedback import score_ceo_against_market
from world.market_probe import probe_market_regime
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
    market = probe_market_regime()
    results = []

    for name, profile in CEO_PROFILES.items():
        if not profile["alive"]:
            continue

        opinion = ceo_debate(ai_text, name, profile)
        market_score = score_ceo_against_market(opinion, market)

        opinion["market_score"] = market_score
        opinion["regime"] = market["regime"]

        profile["memory"].append(opinion)
        if len(profile["memory"]) > 100:
            profile["memory"] = profile["memory"][-100:]

        results.append(opinion)

    return results


def adjust_ceo_fitness(results: list):
    dead = []

    for r in results:
        ceo = CEO_PROFILES.get(r["ceo"])
        if not ceo:
            continue

        ceo["weight"] += r["market_score"] * 0.15
        ceo["weight"] = max(0.05, min(3.0, ceo["weight"]))

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
