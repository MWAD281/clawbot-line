# evolution/judgment_evolver.py

from memory.judgment_state import update_judgment, JUDGMENT_STATE

EVOLUTION_BUFFER = {
    "risk_hits": 0,
    "stability_hits": 0
}

def evolve_from_ai(ai_text: str):
    text = ai_text.lower()
    inertia = JUDGMENT_STATE["inertia"]

    # 🔥 ฝั่งแตก
    if any(k in text for k in [
        "systemic risk",
        "liquidity shock",
        "credit stress",
        "collapse",
        "crisis"
    ]):
        EVOLUTION_BUFFER["risk_hits"] += 1

    # 🧊 ฝั่งฟื้น
    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing",
        "no systemic risk"
    ]):
        EVOLUTION_BUFFER["stability_hits"] += 1

    # 🔥 โลกแตกง่าย
    if EVOLUTION_BUFFER["risk_hits"] >= max(2, int(2 * inertia)):
        update_judgment(
            global_risk="HIGH",
            worldview="FRAGILE",
            stance="DEFENSIVE",
            inertia_delta=+0.3
        )

        EVOLUTION_BUFFER["risk_hits"] = 0
        EVOLUTION_BUFFER["stability_hits"] = 0

    # 🧊 โลกฟื้นยาก
    if EVOLUTION_BUFFER["stability_hits"] >= int(3 * inertia):
        update_judgment(
            global_risk="MEDIUM",
            worldview="STABLE",
            stance="NEUTRAL",
            inertia_delta=-0.2
        )

        EVOLUTION_BUFFER["stability_hits"] = 0
        EVOLUTION_BUFFER["risk_hits"] = max(
            0, EVOLUTION_BUFFER["risk_hits"] - 1
        )
