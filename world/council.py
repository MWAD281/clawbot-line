# world/council.py

from agents.investor_agents import get_investor_views
from agents.finance_agents import get_finance_views
from memory.judgment_state import overwrite_judgment, get_judgment
from world.debate import run_ceo_debate

from agents.ceo_alpha import ceo_alpha

def run_ceo_debate(user_input: str, world_state: dict):
    """
    เรียก CEO ทุกคนมาโหวต
    (ตอนนี้ยังมีแค่ Alpha)
    """

    votes = []

    votes.append(
        ceo_alpha(user_input, world_state)
    )

    return votes

def council_decide(world_input: dict):
    world_state = get_judgment()

    # 🔥 CEO Debate
    ceo_votes = run_ceo_debate(
        world_input.get("text", ""),
        world_state
    )

    risk_score = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0
    }

    for v in ceo_votes:
        risk = v.get("global_risk", "MEDIUM")
        risk_score[risk] += v.get("confidence", 0.5)

    final_risk = max(risk_score, key=risk_score.get)

    overwrite_judgment({
        "global_risk": final_risk,
        "worldview": "FRAGILE_COMPLEX_SYSTEM" if final_risk == "HIGH" else "MIXED",
        "stance": "CAUTIOUS" if final_risk != "LOW" else "NEUTRAL",
        "source": "CEO_DEBATE",
        "last_votes": ceo_votes
    })

    return {
        "final_risk": final_risk,
        "votes": ceo_votes,
        "score": risk_score
    }
