# evolution/judgment_evolver.py

from memory.judgment_state import update_judgment

# 🧬 เก็บแรงกระแทกของโลก
EVOLUTION_BUFFER = {
    "risk_hits": 0,
    "crisis_hits": 0,
    "stability_hits": 0   # 🆕
}

def evolve_from_ai(ai_text: str):
    text = ai_text.lower()

    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing",
        "no systemic risk"
    ]):
        
    EVOLUTION_BUFFER["stability_hits"] += 1

    # 🔥 threshold (แบบดุดัน = 2)
    if EVOLUTION_BUFFER["risk_hits"] >= 2:
        update_judgment(
            global_risk="HIGH",
            worldview="FRAGILE",
            stance="DEFENSIVE"
        )

        # reset กันระเบิด
        EVOLUTION_BUFFER["risk_hits"] = 0
