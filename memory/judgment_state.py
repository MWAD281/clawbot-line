# memory/judgment_state.py

JUDGMENT_STATE = {
    "global_risk": "UNKNOWN",
    "worldview": "UNSET",
    "stance": "NEUTRAL",
    "inertia": 1.0   # ยิ่งสูง โลกยิ่งเปลี่ยนยาก
}

def update_judgment(global_risk, worldview, stance, inertia_delta=0.0):
    JUDGMENT_STATE["global_risk"] = global_risk
    JUDGMENT_STATE["worldview"] = worldview
    JUDGMENT_STATE["stance"] = stance

    # inertia เปลี่ยนแบบสะสม
    JUDGMENT_STATE["inertia"] = max(
        0.5,
        min(3.0, JUDGMENT_STATE["inertia"] + inertia_delta)
    )
