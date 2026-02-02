# memory/judgment_state.py

_JUDGMENT_STATE = {
    "global_risk": "MEDIUM",
    "worldview": "MIXED",
    "stance": "NEUTRAL",
    "source": "BOOT",
    "inertia": 1.0
}

def get_judgment() -> dict:
    return _JUDGMENT_STATE.copy()

def overwrite_judgment(new_state: dict):
    _JUDGMENT_STATE.update(new_state)

# ✅ FIX: alias ให้ agent_evolver ใช้ได้
def save_judgment(partial_state: dict):
    """
    Save incremental judgment updates (agent-level)
    Currently same behavior as overwrite_judgment
    """
    overwrite_judgment(partial_state)
