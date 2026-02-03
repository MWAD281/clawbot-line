# agents/ceo_council.py

from typing import List, Dict

CEO_PROFILES = [
    {
        "name": "Defensive_CEO",
        "bias": "risk_downside",
        "weight": 1.0
    },
    {
        "name": "Aggressive_CEO",
        "bias": "growth_upside",
        "weight": 1.0
    },
    {
        "name": "Systemic_CEO",
        "bias": "systemic_risk",
        "weight": 1.2
    }
]


def ceo_interpret(ai_raw: dict, profile: dict) -> Dict:
    """
    แต่ละ CEO แปลผลโลกในมุมตัวเอง
    """
    text = str(ai_raw).lower()

    score = 0
    risk = 0.5

    if profile["bias"] == "risk_downside":
        if "risk" in text or "war" in text:
            score -= 0.6
            risk += 0.2

    elif profile["bias"] == "growth_upside":
        if "growth" in text or "opportunity" in text:
            score += 0.6
            risk -= 0.1

    elif profile["bias"] == "systemic_risk":
        if "system" in text or "collapse" in text:
            score -= 0.7
            risk += 0.3

    return {
        "ceo": profile["name"],
        "score": score,
        "global_risk": min(1.0, max(0.0, risk)),
        "weight": profile["weight"]
    }


def run_ceo_council(ai_raw: dict) -> List[Dict]:
    """
    ให้ CEO ทุกตัวออกความเห็น
    """
    opinions = []
    for profile in CEO_PROFILES:
        opinions.append(ceo_interpret(ai_raw, profile))
    return opinions
