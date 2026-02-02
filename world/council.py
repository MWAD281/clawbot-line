# world/council.py

from memory.judgment_state import overwrite_judgment, get_judgment
from memory.agent_weights import get_weight, is_muted
from world.debate import run_ceo_debate


def council_decide(world_input: dict):
    world_state = get_judgment()

    # 🔥 CEO Debate (เรียกจาก debate engine เท่านั้น)
    ceo_votes = run_ceo_debate(
        world_input.get("text", ""),
        world_state
    )

    risk_score = {
        "LOW": 0.0,
        "MEDIUM": 0.0,
        "HIGH": 0.0
    }

    # 🧠 Decide final risk
    if all(v == 0 for v in risk_score.values()):
        # 🧟 fallback: ไม่มี CEO ที่ active
        final_risk = world_state.get("global_risk", "MEDIUM")
    else:
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
