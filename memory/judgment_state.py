# memory/judgment_state.py

JUDGMENT_STATE = {
    "global_risk": "UNKNOWN",
    "worldview": "UNSET",
    "stance": "NEUTRAL",
    "inertia": 1.0
}

def update_judgment(
    global_risk: str,
    worldview: str,
    stance: str,
    inertia_delta: float = 0.0
) -> None:
    JUDGMENT_STATE["global_risk"] = global_risk
    JUDGMENT_STATE["worldview"] = worldview
    JUDGMENT_STATE["stance"] = stance
    JUDGMENT_STATE["inertia"] = max(
        0.5,
        min(5.0, JUDGMENT_STATE["inertia"] + inertia_delta)
    )

def get_judgment() -> dict:
    return JUDGMENT_STATE.copy()
