# memory/judgment_state.py

JUDGMENT_STATE = {
    "global_risk": "UNKNOWN",   # LOW | MEDIUM | HIGH
    "worldview": "UNSET",       # STABLE | FRAGILE | CRISIS
    "stance": "NEUTRAL",        # OFFENSIVE | DEFENSIVE
    "inertia": 1.0              # 🆕 ยิ่งสูง ยิ่งเปลี่ยนยาก
}

def update_judgment(
    global_risk: str,
    worldview: str,
    stance: str,
    inertia_delta: float | None = None
) -> None:
    JUDGMENT_STATE["global_risk"] = global_risk
    JUDGMENT_STATE["worldview"] = worldview
    JUDGMENT_STATE["stance"] = stance

    if inertia_delta is not None:
        JUDGMENT_STATE["inertia"] = max(
            0.5,
            min(3.0, JUDGMENT_STATE["inertia"] + inertia_delta)
        )

def get_judgment() -> dict:
    return JUDGMENT_STATE.copy()
