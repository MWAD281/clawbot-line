# memory/judgment_drift.py

from copy import deepcopy
from typing import Dict

# =========================
# DRIFT CONFIG
# =========================

BASE_DRIFT_RATE = 0.15
MAX_DRIFT = 0.35
MIN_DRIFT = 0.03


# =========================
# HELPERS
# =========================

def clamp(val: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, val))


def risk_to_numeric(risk: str) -> float:
    return {
        "LOW": 0.2,
        "MEDIUM": 0.5,
        "HIGH": 0.8,
        "EXTREME": 1.0
    }.get(risk.upper(), 0.5)


def numeric_to_risk(v: float) -> str:
    if v < 0.3:
        return "LOW"
    if v < 0.6:
        return "MEDIUM"
    if v < 0.85:
        return "HIGH"
    return "EXTREME"


# =========================
# CORE DRIFT LOGIC
# =========================

def apply_judgment_drift(
    current: Dict,
    incoming_risk_score: float,
    confidence: float = 0.5
) -> Dict:
    """
    Slowly drift judgment instead of snapping.
    """

    new_state = deepcopy(current)

    inertia = float(current.get("inertia", 1.0))
    current_risk = risk_to_numeric(current.get("global_risk", "MEDIUM"))

    # dynamic drift speed
    drift_rate = BASE_DRIFT_RATE * confidence / inertia
    drift_rate = clamp(drift_rate, MIN_DRIFT, MAX_DRIFT)

    # move risk slightly toward incoming
    drifted_risk = current_risk + (incoming_risk_score - current_risk) * drift_rate
    drifted_risk = clamp(drifted_risk, 0.0, 1.0)

    # update judgment
    new_state["global_risk"] = numeric_to_risk(drifted_risk)

    # worldview + stance logic
    if drifted_risk > 0.75:
        new_state["worldview"] = "defensive"
        new_state["stance"] = "RISK_OFF"
    elif drifted_risk < 0.35:
        new_state["worldview"] = "constructive"
        new_state["stance"] = "RISK_ON"
    else:
        new_state["worldview"] = "neutral"
        new_state["stance"] = "NEUTRAL"

    # inertia slowly increases (memory hardening)
    new_state["inertia"] = clamp(inertia + 0.05, 0.8, 3.0)

    return new_state
