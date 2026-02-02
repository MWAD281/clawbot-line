# memory/judgment_state.py

JUDGMENT_STATE = {
    "global_risk": "UNKNOWN",   # LOW | MEDIUM | HIGH
    "worldview": "UNSET",       # STABLE | FRAGILE | CRISIS
    "stance": "NEUTRAL"         # OFFENSIVE | DEFENSIVE
}

def update_judgment(global_risk: str, worldview: str, stance: str) -> None:
    JUDGMENT_STATE["global_risk"] = global_risk
    JUDGMENT_STATE["worldview"] = worldview
    JUDGMENT_STATE["stance"] = stance

def get_judgment() -> dict:
    return JUDGMENT_STATE.copy()  # ป้องกันโดนแก้จากภายนอก
