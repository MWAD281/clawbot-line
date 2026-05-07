# evolution/ceo_rebirth.py
# 🧬 Phase 11.9 – CEO Death & Rebirth (Full Darwinism)

import random
import time

from memory.agent_weights import (
    get_all_agents,
    get_weight,
    set_weight,
    is_muted,
    unmute_agent,
    delete_agent
)

from agents.ceo_profile import generate_ceo_profile

# -------------------------
# CONFIG
# -------------------------

DEATH_WEIGHT_THRESHOLD = 0.12     # ต่ำกว่านี้ = ตาย
REBIRTH_POOL_SIZE = 3             # เอา top CEO มากี่ตัวเป็น DNA pool
INITIAL_WEIGHT = 0.6              # weight เริ่มต้นของ CEO ใหม่


# -------------------------
# CORE
# -------------------------

def run_ceo_rebirth_cycle():
    """
    ตรวจสอบ CEO ทั้งระบบ
    - ใครควรตาย → remove
    - สร้าง CEO ใหม่แทน
    """

    agents = get_all_agents()
    if not agents:
        print("[REBIRTH] No agents found")
        return

    dead_agents = []
    alive_agents = []

    # -------------------------
    # CLASSIFY
    # -------------------------
    for agent_id in agents:
        weight = get_weight(agent_id)

        if weight < DEATH_WEIGHT_THRESHOLD:
            dead_agents.append(agent_id)
        else:
            alive_agents.append(agent_id)

    if not dead_agents:
        return

    print(f"[REBIRTH] Agents dying: {dead_agents}")

    # -------------------------
    # SELECT PARENTS (TOP CEO)
    # -------------------------
    alive_agents.sort(
        key=lambda a: get_weight(a),
        reverse=True
    )
    parent_pool = alive_agents[:REBIRTH_POOL_SIZE]

    # -------------------------
    # EXECUTE DEATH
    # -------------------------
    for agent_id in dead_agents:
        delete_agent(agent_id)

    # -------------------------
    # REBIRTH
    # -------------------------
    for _ in dead_agents:
        parent = random.choice(parent_pool) if parent_pool else None
        new_agent_id, profile = generate_ceo_profile(parent)

        set_weight(new_agent_id, INITIAL_WEIGHT)
        unmute_agent(new_agent_id)

        print(
            f"[REBIRTH] New CEO born: {new_agent_id} "
            f"(parent={parent})"
        )


# -------------------------
# MANUAL TEST
# -------------------------

def manual_rebirth_test():
    """
    ใช้ trigger manual ได้
    """
    run_ceo_rebirth_cycle()
