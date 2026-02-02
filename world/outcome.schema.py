# world/outcome_schema.py

def normalize_outcome(raw: dict) -> dict:
    """
    แปลง outcome ให้เป็น schema กลาง
    """
    return {
        "market_crash": raw.get("market_crash", False),
        "volatility_spike": raw.get("volatility_spike", False),
        "liquidity_freeze": raw.get("liquidity_freeze", False),
        "risk_assets_down": raw.get("risk_assets_down", False),
        "timestamp": raw.get("timestamp")
    }
