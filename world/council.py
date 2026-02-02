# world/council.py

from memory.judgment_state import overwrite_judgment, get_judgment
from memory.agent_weights import get_weight, is_muted, adjust_weight
from memory.agent_lifecycle import record_performance, should_die
from world.debate import run_ceo_debate
from world.regime import apply_regime_shift


def council_decide(world_input: dict):
    """
    Central decision engine ของโลก (Phase 10.1 + 11)
    - CEO มี personality + memory
    - ถ่วงน้ำหนักด้วย Darwinism
    - CEO ตาย / mute ได้
    - faction dominance
    - regime shift
    """

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

    extinction_events = []

    # 🧮 Aggregate votes
    for v in ceo_votes:
        agent_id = v.get("agent_id")
        faction = v.get("faction", "UNKNOWN")
        risk = v.get("global_risk", "MEDIUM")
        confidence = v.get("confidence", 0.5)

        # 🔇 agent ที่ถูก mute ไม่มีเสียง
        if not agent_id or is_muted(agent_id):
            continue

        weight = get_weight(agent_id)
        impact = confidence * weight

        # รวมคะแนน risk
        risk_score[risk] += impact

        # รวมคะแนน faction
        faction_score.setdefault(faction, 0.0)
        faction_score[faction] += impact

        # 🧬 Darwinism: บันทึกผลงาน
        record_performance(agent_id, impact)

        # ☠️ ตรวจการตายของ CEO
        if should_die(agent_id):
            adjust_weight(agent_id, -10)  # mute ถาวร
            extinction_events.append(agent_id)

    # 🧠 Decide final risk
    if all(v == 0 for v in risk_score.values()):
        # 🧟 fallback: ไม่มี CEO ที่ active
        final_risk = world_state.get("global_risk", "MEDIUM")
    else:
        final_risk = max(risk_score, key=risk_score.get)

    # 🏛️ Decide dominant faction
    dominant_faction = (
        max(faction_score, key=faction_score.get)
        if faction_score else "UNKNOWN"
    )

    # 🌋 Regime Shift
    apply_regime_shift(dominant_faction)

    # 🌍 Commit world judgment
    overwrite_judgment({
        "global_risk": final_risk,
        "worldview": (
            "FRAGILE_COMPLEX_SYSTEM"
            if final_risk == "HIGH"
            else "MIXED"
        ),
        "stance": (
            "CAUTIOUS"
            if final_risk != "LOW"
            else "NEUTRAL"
        ),
        "source": "CEO_DEBATE",
        "dominant_faction": dominant_faction,
        "extinctions": extinction_events,
        "last_votes": ceo_votes
    })

    return {
        "final_risk": final_risk,
        "dominant_faction": dominant_faction,
        "votes": ceo_votes,
        "risk_score": risk_score,
        "factions": faction_score,
        "extinctions": extinction_events
    }
