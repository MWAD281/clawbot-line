# world/market_probe.py

def probe_market_regime() -> dict:
    """
    Market proxy (no real trading)
    ใช้แทน market truth ชั่วคราว
    """

    # 🔮 mock regime (Phase 12 จะต่อ API จริง)
    regime = "RISK_OFF"   # RISK_ON / RISK_OFF / NEUTRAL

    if regime == "RISK_ON":
        return {
            "regime": "RISK_ON",
            "reward_bias": 0.6,
            "penalty_bias": -0.2
        }

    if regime == "RISK_OFF":
        return {
            "regime": "RISK_OFF",
            "reward_bias": -0.4,
            "penalty_bias": 0.6
        }

    return {
        "regime": "NEUTRAL",
        "reward_bias": 0.0,
        "penalty_bias": 0.0
    }
