from memory.agent_weights import adjust_weight

def evolve_agents(judgment: dict, outcome: dict):
    """
    Darwinism: ปรับน้ำหนัก agent จากผลลัพธ์จริง
    """

    if "last_votes" not in judgment:
        return

    for v in judgment["last_votes"]:
        agent = v.get("agent_id")
        risk = v.get("global_risk")

        if not agent or not risk:
            continue

        # 🔥 ตลาดพัง → คนที่เตือน HIGH ถูก
        if outcome.get("market_crash") and risk == "HIGH":
            adjust_weight(agent, +0.3)

        # ❌ ตลาดพัง → คนที่บอก LOW ผิด
        elif outcome.get("market_crash") and risk == "LOW":
            adjust_weight(agent, -0.4)

        # 🧊 ตลาดนิ่ง → คนที่กลัวเกินไป
        elif not outcome.get("market_crash") and risk == "HIGH":
            adjust_weight(agent, -0.1)
