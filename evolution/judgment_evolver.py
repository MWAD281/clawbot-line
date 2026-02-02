# evolution/judgment_evolver.py

from memory.judgment_state import update_judgment

def evolve_from_ai(ai_text: str) -> None:
    """
    อ่าน Judgment จากคำตอบ AI แล้ว update global judgment state
    """

    text = ai_text.lower()

    # default
    global_risk = "MEDIUM"
    worldview = "FRAGILE"
    stance = "DEFENSIVE"

    # ---- Risk detection ----
    if any(k in text for k in ["systemic", "crisis", "แตกหัก", "collapse"]):
        global_risk = "HIGH"
        worldview = "CRISIS"
        stance = "DEFENSIVE"

    elif any(k in text for k in ["เสถียร", "stabilizing", "soft landing"]):
        global_risk = "LOW"
        worldview = "STABLE"
        stance = "OFFENSIVE"

    # ---- Stance override ----
    if any(k in text for k in ["opportunity", "accumulate", "risk-on"]):
        stance = "OFFENSIVE"

    if any(k in text for k in ["protect", "risk-off", "preserve"]):
        stance = "DEFENSIVE"

    update_judgment(
        global_risk=global_risk,
        worldview=worldview,
        stance=stance
    )
