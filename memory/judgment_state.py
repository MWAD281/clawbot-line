# memory/judgment_state.py

JUDGMENT_STATE = {
    "global_risk": "MEDIUM",     # โลกมีความเสี่ยงเชิงระบบอยู่แล้ว
    "worldview": "FRAGILE",      # เปราะบาง แต่ยังไม่แตก
    "stance": "DEFENSIVE"        # default = ระวังตัว
}

def update_judgment(global_risk: str, worldview: str, stance: str) -> None:
    JUDGMENT_STATE["global_risk"] = global_risk
    JUDGMENT_STATE["worldview"] = worldview
    JUDGMENT_STATE["stance"] = stance

def get_judgment() -> dict:
    return JUDGMENT_STATE.copy()  # ป้องกันโดนแก้จากภายนอก
