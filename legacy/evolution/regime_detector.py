# evolution/regime_detector.py

REGIME_SCORES = {
    "RISK_ON": 0,
    "RISK_OFF": 0,
    "STAGFLATION": 0,
    "CHAOS": 0
}

CURRENT_REGIME = {
    "name": "NEUTRAL",
    "inertia": 0.0
}


def infer_regime(judgment: dict) -> str:
    risk = judgment.get("global_risk", 0.5)
    stance = judgment.get("stance")
    worldview = judgment.get("worldview")

    if risk > 0.7 and stance == "RISK_OFF":
        return "CHAOS"

    if risk > 0.6 and worldview == "defensive":
        return "RISK_OFF"

    if risk < 0.45 and stance == "RISK_ON":
        return "RISK_ON"

    if risk > 0.5 and stance == "WAIT":
        return "STAGFLATION"

    return "NEUTRAL"


def update_regime(judgment: dict) -> str:
    global CURRENT_REGIME

    detected = infer_regime(judgment)

    # decay ทุก regime
    for k in REGIME_SCORES:
        REGIME_SCORES[k] *= 0.9

    if detected in REGIME_SCORES:
        REGIME_SCORES[detected] += 1.0

    dominant = max(REGIME_SCORES, key=REGIME_SCORES.get)

    # inertia logic
    if dominant == CURRENT_REGIME["name"]:
        CURRENT_REGIME["inertia"] += 0.3
    else:
        CURRENT_REGIME["inertia"] -= 0.4

    if CURRENT_REGIME["inertia"] < 0:
        CURRENT_REGIME = {
            "name": dominant,
            "inertia": 1.0
        }

    judgment["regime"] = CURRENT_REGIME["name"]
    judgment["regime_inertia"] = round(CURRENT_REGIME["inertia"], 2)

    return CURRENT_REGIME["name"]
