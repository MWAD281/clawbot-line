# evolution/judgment_evolver.py

from memory.judgment_state import update_judgment

# 🧬 เก็บแรงกระแทกของโลก
EVOLUTION_BUFFER = {
    "risk_hits": 0,
    "crisis_hits": 0,
    "stability_hits": 0
}

def evolve_from_ai(ai_text: str):
    text = ai_text.lower()

    # 🔥 ฝั่งเสี่ยง / แตกหัก
    if any(k in text for k in [
        "systemic risk",
        "liquidity shock",
        "credit stress",
        "collapse",
        "crisis"
    ]):
        EVOLUTION_BUFFER["risk_hits"] += 1

    # 🧊 ฝั่งผ่อนคลาย / เสถียร
    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing", 
        "no systemic risk"
    ]):
        EVOLUTION_BUFFER["stability_hits"] += 1

    # 🔥 โลกเริ่มแตก (ดุดัน)
    if EVOLUTION_BUFFER["risk_hits"] >= 2:
        update_judgment(
            global_risk="HIGH",
            worldview="FRAGILE",
            stance="DEFENSIVE"
        )
        EVOLUTION_BUFFER["risk_hits"] = 0
        EVOLUTION_BUFFER["stability_hits"] = 0  # reset ฝั่งตรงข้าม

    # 🧊 โลกเริ่มผ่อนคลาย (ต้องสะสม)
    if EVOLUTION_BUFFER["stability_hits"] >= 3:
        update_judgment(
            global_risk="MEDIUM",
            worldview="STABLE",
            stance="NEUTRAL"
        )

        EVOLUTION_BUFFER["stability_hits"] = 0
        EVOLUTION_BUFFER["risk_hits"] = max(
            0, EVOLUTION_BUFFER["risk_hits"] - 1
        )
