# agents/ceo_beta.py
# CEO Beta — Liquidity Hunter

def ceo_beta(user_input: str, world_state: dict):
    risk = world_state.get("global_risk", "MEDIUM")

    if risk in ["HIGH", "LATENT_SYSTEMIC_RISK"]:
        return {
            "agent_id": "CEO_BETA",
            "faction": "LIQUIDITY",
            "global_risk": "MEDIUM",
            "confidence": 0.7,
            "stance": "OPPORTUNISTIC",
            "reason": "Panic creates liquidity pockets and mispricing"
        }

    return {
        "agent_id": "CEO_BETA",
        "faction": "LIQUIDITY",
        "global_risk": "LOW",
        "confidence": 0.6,
        "stance": "OPPORTUNISTIC",
        "reason": "Risk premium compressed; upside limited"
    }
