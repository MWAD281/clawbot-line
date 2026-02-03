# agents/ceo_debate.py

def ceo_debate(ai_text: str, name: str, profile: dict) -> dict:
    """
    ให้ CEO แสดงความเห็นเป็นภาษา (เหตุผล)
    """
    bias = profile.get("bias", "neutral")

    if bias == "risk_downside":
        opinion = (
            f"{name}: มุมมองนี้มี downside risk สูง "
            "ควรระวัง tail risk และ systemic shock"
        )
        score = -0.5
        risk = 0.7

    elif bias == "growth_upside":
        opinion = (
            f"{name}: เห็น opportunity เชิงโครงสร้าง "
            "risk อยู่ในระดับรับได้"
        )
        score = 0.6
        risk = 0.4

    elif bias == "systemic_risk":
        opinion = (
            f"{name}: โครงสร้างระบบเปราะบาง "
            "liquidity และ feedback loop น่ากังวล"
        )
        score = -0.7
        risk = 0.8

    else:
        opinion = f"{name}: ยังไม่เห็น signal ชัด"
        score = 0.0
        risk = 0.5

    return {
        "ceo": name,
        "opinion": opinion,
        "score": score,
        "global_risk": risk,
        "weight": profile.get("weight", 1.0)
    }
