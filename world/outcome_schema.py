# world/outcome_schema.py

def normalize_outcome(result: dict) -> dict:
    """
    Normalize council/world output before sending to API response
    """
    return {
        "risk": result.get("final_risk", "MEDIUM"),
        "stance": result.get("stance", "UNKNOWN"),
        "source": result.get("source", "SYSTEM"),
        "votes": result.get("votes", {}),
        "score": result.get("score", {})
    }
