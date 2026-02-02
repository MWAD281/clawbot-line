# evolution/judgment_evolver.py

def evolve_judgment(judgment: dict, outcome: dict) -> dict:
    """
    ปรับ worldview ของระบบจาก outcome โลกจริง
    """

    score = outcome.get("score", 0)
    global_risk = outcome.get("global_risk", outcome.get("risk", 0.5))

    # ค่า default
    judgment.setdefault("worldview", "neutral")
    judgment.setdefault("confidence", 0.5)

    # 🔁 Logic การเปลี่ยน worldview
    if score < -0.5 or global_risk > 0.7:
        judgment["worldview"] = "defensive"
        judgment["confidence"] = max(0.1, judgment["confidence"] - 0.1)

    elif score > 0.5 and global_risk < 0.4:
        judgment["worldview"] = "aggressive"
        judgment["confidence"] = min(0.9, judgment["confidence"] + 0.1)

    else:
        judgment["worldview"] = "neutral"

    return judgment
