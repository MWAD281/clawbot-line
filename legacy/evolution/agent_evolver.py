# evolution/agent_evolver.py

from memory.agent_weights import adjust_weight, revive_agent
from memory.agent_performance import record_result
from memory.judgment_state import save_judgment
from evolution.judgment_evolver import evolve_judgment


def evolve_agents(judgment: dict, outcome: dict):
    """
    Darwinism: ปรับน้ำหนัก agent จากผลลัพธ์จริง
    """

    # 🧠 evolve โลกก่อน
    judgment = evolve_judgment(judgment, outcome)
    save_judgment(judgment)

    if "last_votes" not in judgment:
        return

    market_crash = outcome.get("market_crash", False)

    for v in judgment["last_votes"]:
        agent = v.get("agent_id")
        risk = v.get("global_risk")

        if not agent or not risk:
            continue

        # ✅ ตัดสินถูก / ผิด
        correct = (
            market_crash and risk == "HIGH"
        ) or (
            not market_crash and risk == "LOW"
        )

        record_result(agent, correct)

        # ⚖️ ปรับน้ำหนัก
        if correct:
            adjust_weight(agent, +0.2)
        else:
            adjust_weight(agent, -0.3)

        # 🧟 revive ถ้า regime เปลี่ยน
        if judgment.get("worldview") == "aggressive":
            revive_agent(agent, weight=0.4)
