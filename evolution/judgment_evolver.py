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

    if any(k in text for k in [
        "systemic risk",
        "liquidity shock",
        "credit stress",
        "collapse",
        "crisis",
        "bank run",
        "contagion"
    ]):
        EVOLUTION_BUFFER["risk_hits"] += 1

    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing"
    ]):
        EVOLUTION_BUFFER["stability_hits"] += 1

    if EVOLUTION_BUFFER["risk_hits"] >= int(2 * inertia):
        overwrite_judgment({
            "global_risk": "HIGH",
            "worldview": "SYSTEMIC_STRESS",
            "stance": "DEFENSIVE",
            "inertia": inertia + 0.5
        })
        EVOLUTION_BUFFER["risk_hits"] = 0
        EVOLUTION_BUFFER["stability_hits"] = 0
        return

    if EVOLUTION_BUFFER["stability_hits"] >= int(4 * inertia):
        overwrite_judgment({
            "global_risk": "MEDIUM",
            "worldview": "STABILIZING",
            "stance": "CAUTIOUS",
            "inertia": max(1.0, inertia - 0.1)
        })
        EVOLUTION_BUFFER["stability_hits"] = 0
