# evolution/judgment_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment

EVOLUTION_BUFFER = {
    "risk_hits": 0,
    "stability_hits": 0
}

def evolve_from_ai(ai_text: str):
    text = ai_text.lower()
    state = get_judgment()

    inertia = state.get("inertia", 1.0)

    # 🔥 ฝั่งสัญญาณโลกแตก
    if any(k in text for k in [
        "systemic risk",
        "liquidity shock",
        "credit stress",
        "collapse",
        "crisis"
    ]):
        EVOLUTION_BUFFER["risk_hits"] += 1

    # 🧊 ฝั่งสัญญาณฟื้น
    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing",
        "no systemic risk"
    ]):
        EVOLUTION_BUFFER["stability_hits"] += 1

    # 🔥 โลกแตกง่าย (fear-first)
    if EVOLUTION_BUFFER["risk_hits"] >= max(2, int(2 * inertia)):
        state.update({
            "global_risk": "HIGH",
            "worldview": "FRAGILE",
            "stance": "DEFENSIVE",
            "inertia": inertia + 0.3
        })

        overwrite_judgment(state)

        EVOLUTION_BUFFER["risk_hits"] = 0
        EVOLUTION_BUFFER["stability_hits"] = 0
        return

    # 🧊 โลกฟื้นยาก
    if EVOLUTION_BUFFER["stability_hits"] >= int(3 * inertia):
        state.update({
            "global_risk": "MEDIUM",
            "worldview": "STABLE",
            "stance": "NEUTRAL",
            "inertia": max(0.5, inertia - 0.2)
        })

        overwrite_judgment(state)

        EVOLUTION_BUFFER["stability_hits"] = 0
        EVOLUTION_BUFFER["risk_hits"] = max(
            0, EVOLUTION_BUFFER["risk_hits"] - 1
        )
