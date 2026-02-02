# world/council.py

from memory.judgment_state import overwrite_judgment, get_judgment
from memory.agent_weights import get_weight   # ✅ ต้องเพิ่มบรรทัดนี้
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

    for v in ceo_votes:
        agent_id = v.get("agent_id")
        risk = v.get("global_risk", "MEDIUM")

        weight = get_weight(agent_id)
        confidence = v.get("confidence", 0.5)

        risk_score[risk] += confidence * weight

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
