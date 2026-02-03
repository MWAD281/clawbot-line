# agents/ceo_council.py

from typing import List, Dict
from agents.ceo_genome import spawn_ceo, should_die
import uuid

# 🧬 CEO population
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


def ceo_interpret(ai_raw: dict, name: str, profile: dict) -> Dict:
    text = str(ai_raw).lower()
    score = 0
    risk = 0.5

    bias = profile["bias"]

    if bias == "risk_downside" and any(k in text for k in ["risk", "war", "collapse"]):
        score -= 0.6
        risk += 0.2

    if bias == "growth_upside" and any(k in text for k in ["growth", "opportunity"]):
        score += 0.6
        risk -= 0.1

    if bias == "systemic_risk" and any(k in text for k in ["system", "liquidity", "collapse"]):
        score -= 0.7
        risk += 0.3

    # 🧠 save memory
    profile["memory"].append({
        "score": score,
        "risk": risk
    })

    # จำกัด memory
    if len(profile["memory"]) > 50:
        profile["memory"] = profile["memory"][-50:]

    return {
        "ceo": name,
        "score": score,
        "global_risk": min(1.0, max(0.0, risk)),
        "weight": profile["weight"]
    }


def run_ceo_council(ai_raw: dict) -> List[Dict]:
    opinions = []

    for name, profile in CEO_PROFILES.items():
        if not profile["alive"]:
            continue
        opinions.append(
            ceo_interpret(ai_raw, name, profile)
        )

    return opinions


def adjust_ceo_fitness(results: List[Dict]):
    """
    Darwinism:
    - ปรับ weight
    - CEO ตาย → เกิดใหม่
    """

    dead_ceos = []

    for r in results:
        ceo = CEO_PROFILES.get(r["ceo"])
        if not ceo:
            continue

        ceo["weight"] += r["score"] * 0.1
        ceo["weight"] = max(0.05, min(2.0, ceo["weight"]))

        if should_die(ceo):
            ceo["alive"] = False
            dead_ceos.append(r["ceo"])

    # ♻️ Rebirth
    for dead in dead_ceos:
        parent = CEO_PROFILES.get(dead)
        if not parent:
            continue

        new_name = f"CEO_{uuid.uuid4().hex[:6]}"
        CEO_PROFILES[new_name] = spawn_ceo(dead, parent)
