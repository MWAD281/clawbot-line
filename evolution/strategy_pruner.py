# evolution/strategy_pruner.py
# 🔥 Phase 11.8 – Strategy Pruning (Darwinism Core)

from memory.agent_weights import (
    get_weight,
    set_weight,
    mute_agent
)

# -------------------------
# CONFIG
# -------------------------

MIN_WEIGHT = 0.3          # ต่ำกว่านี้ = เสียงแทบไม่มีค่า
PRUNE_THRESHOLD = -0.6    # score แพ้หนัก
DECAY_RATE = 0.15         # ลดน้ำหนักต่อรอบ
MUTE_THRESHOLD = 0.15     # ต่ำกว่านี้ = mute


# -------------------------
# CORE LOGIC
# -------------------------

def prune_strategies(votes: list, final_risk: str):
    """
    ปรับน้ำหนัก CEO ตามผลลัพธ์จริงของโลก
    - votes: ผลโหวตจาก CEO แต่ละตัว
    - final_risk: risk ที่โลกตัดสินสุดท้าย
    """

    for v in votes:
        agent_id = v.get("agent_id")
        predicted_risk = v.get("global_risk")
        confidence = v.get("confidence", 0.5)

        if not agent_id or not predicted_risk:
            continue

        current_weight = get_weight(agent_id)

        # -------------------------
        # WIN / LOSE CHECK
        # -------------------------
        if predicted_risk == final_risk:
            # 🎯 ทายถูก → reward เล็กน้อย
            new_weight = min(1.5, current_weight + (0.05 * confidence))
            set_weight(agent_id, new_weight)
            continue

        # ❌ ทายผิด
        penalty = DECAY_RATE * confidence
        new_weight = current_weight - penalty

        # -------------------------
        # APPLY PRUNE
        # -------------------------
        if new_weight < MUTE_THRESHOLD:
            mute_agent(agent_id)
            set_weight(agent_id, max(new_weight, 0.05))
            print(f"[PRUNE] {agent_id} muted (weight={new_weight:.2f})")

        elif new_weight < MIN_WEIGHT:
            set_weight(agent_id, new_weight)
            print(f"[PRUNE] {agent_id} weakened (weight={new_weight:.2f})")

        else:
            set_weight(agent_id, new_weight)


# -------------------------
# DEBUG / MANUAL TRIGGER
# -------------------------

def manual_prune_test():
    """
    ใช้ทดสอบ pruning แบบ manual
    """
    sample_votes = [
        {"agent_id": "Alpha", "global_risk": "HIGH", "confidence": 0.8},
        {"agent_id": "Beta", "global_risk": "LOW", "confidence": 0.6},
        {"agent_id": "Gamma", "global_risk": "MEDIUM", "confidence": 0.5},
    ]

    prune_strategies(sample_votes, final_risk="HIGH")
