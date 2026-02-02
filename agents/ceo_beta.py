# agents/ceo_beta.py

def ceo_beta(user_input: str, world_state: dict):
    """
    CEO Beta — Opportunistic
    มอง risk เป็นโอกาส ถ้า panic สูงเกินไปจะสวน
    """

    global_risk = world_state.get("global_risk", "MEDIUM")

    # ถ้าโลกกลัวมาก → Beta จะสวน
    if global_risk in ["HIGH", "LATENT_SYSTEMIC_RISK"]:
        return {
            "ceo": "BETA",
            "global_risk": "MEDIUM",
            "confidence": 0.7,
            "reason": "Panic risk elevated, opportunity forming"
        }

    # ถ้าโลกดูนิ่ง → Beta จะเริ่มระวัง
    return {
        "ceo": "BETA",
        "global_risk": "LOW",
        "confidence": 0.6,
        "reason": "Risk premium compressed, upside limited"
    }
