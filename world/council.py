# world/council.py

from agents.investor_agents import get_investor_views
from agents.finance_agents import get_finance_views
from memory.judgment_state import overwrite_judgment, get_judgment

def council_decide(world_input: dict):
    """
    รวมเสียงจาก agent ทุกฝั่ง แล้วตัดสิน worldview กลาง
    """

    world_state = get_judgment()

    investor_views = get_investor_views(world_input, world_state)
    finance_views = get_finance_views(world_input, world_state)

    all_views = investor_views + finance_views

    risk_score = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0
    }

    for v in all_views:
        risk = v.get("global_risk", "MEDIUM")

        if risk not in risk_score:
            risk = "MEDIUM"

    risk_score[risk] += v.get("weight", 1.0)

    final_risk = max(risk_score, key=risk_score.get)

    overwrite_judgment({
        "global_risk": final_risk,
        "worldview": "FRAGILE_COMPLEX_SYSTEM" if final_risk == "HIGH" else "MIXED",
        "stance": "CAUTIOUS" if final_risk != "LOW" else "NEUTRAL",
        "source": "COUNCIL"
    })

    return {
        "final_risk": final_risk,
        "votes": all_views,
        "score": risk_score
    }
