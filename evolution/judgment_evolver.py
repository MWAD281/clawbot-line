# evolution/judgment_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment

EVOLUTION_BUFFER = {
    "risk_hits": 0,
    "stability_hits": 0
}

def evolve_from_ai(ai_text: str):
    text = ai_text.lower()

    # ✅ ดึง state ล่าสุดจริง ๆ
    state = get_judgment()
    inertia = state.get("inertia", 1.0)

    # 🔥 trigger ฝั่งเสี่ยง
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

    # 🧊 trigger ฝั่งฟื้น
    if any(k in text for k in [
        "soft landing",
        "inflation easing",
        "liquidity improving",
        "policy support",
        "risk stabilizing",
        "no systemic risk"
    ]):
        EVOLUTION_BUFFER["stability_hits"] += 1

    # 🔥 โลกแตก "ง่ายขึ้น" เมื่อ inertia สูง
    if EVOLUTION_BUFFER["risk_hits"] >= max(1, int(2 * inertia)):
        overwrite_judgment({
            "global_risk": "HIGH",
            "worldview": "FRAGILE_SYSTEM",
            "stance": "DEFENSIVE",
            "inertia": inertia + 0.3
        })

        EVOLUTION_BUFFER["risk_hits"] = 0
        EVOLUTION_BUFFER["stability_hits"] = 0

    # 🧊 โลกจะสงบ "ยากมาก" ถ้า inertia สูง
    if EVOLUTION_BUFFER["stability_hits"] >= int(4 * inertia):
        overwrite_judgment({
            "global_risk": "MEDIUM",
            "worldview": "STABILIZING_SYSTEM",
            "stance": "NEUTRAL",
            "inertia": max(1.0, inertia - 0.2)
        })

        EVOLUTION_BUFFER["stability_hits"] = 0
        EVOLUTION_BUFFER["risk_hits"] = max(
            0, EVOLUTION_BUFFER["risk_hits"] - 1
        )
