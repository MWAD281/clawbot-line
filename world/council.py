# world/council.py

from memory.judgment_state import overwrite_judgment, get_judgment
from memory.agent_weights import get_weight, is_muted
from world.debate import run_ceo_debate


def council_decide(world_input: dict):
    world_state = get_judgment()

    # 🔥 CEO Debate
    ceo_votes = run_ceo_debate(
        world_input.get("text", ""),
        world_state
    )

    risk_score = {
        "LOW": 0.0,
        "MEDIUM": 0.0,
        "HIGH": 0.0
    }

    faction_score = {}

    for v in ceo_votes:
        agent_id = v.get("agent_id")
        faction = v.get("faction", "UNKNOWN")
        risk = v.get("global_risk", "MEDIUM")

        if not agent_id or is_muted(agent_id):
            continue

        weight = get_weight(agent_id)
        confidence = v.get("confidence", 0.5)

        risk_score[risk] += confidence * weight
        faction_score.setdefault(faction, 0.0)
        faction_score[faction] += confidence * weight

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
        "dominant_faction": max(faction_score, key=faction_score.get),
        "votes": ceo_votes,
        "score": risk_score,
        "factions": faction_score
    }
