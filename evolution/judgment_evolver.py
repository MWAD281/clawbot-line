# evolution/judgment_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment


def evolve_judgment(judgment: dict, outcome: dict) -> dict:
    """
    ปรับ worldview ของระบบจาก outcome โลกจริง
    """

    # 🧟 HARD GUARD: กัน type พัง
    if not isinstance(judgment, dict):
        print("EVOLVE SKIP: judgment is not dict ->", type(judgment))
        judgment = {}

    score = outcome.get("score", 0)
    global_risk = outcome.get("global_risk", 0.5)

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


def evolve_from_ai(user_text: str, ai_result: dict) -> dict:
    """
    evolve judgment จากผลลัพธ์ AI
    - ดึง judgment จาก memory เอง
    - user_text ใช้สำหรับ future semantic analysis
    """

    # 🧠 โหลด world state ปัจจุบัน
    judgment = get_judgment()

    # 🔎 extract outcome จาก AI (robust)
    if not isinstance(ai_result, dict):
        print("EVOLVE SKIP: ai_result is not dict ->", type(ai_result))
        return judgment

    outcome = {
        "score": ai_result.get("score", 0),
        "global_risk": ai_result.get("global_risk", 0.5)
    }

    new_judgment = evolve_judgment(judgment, outcome)

    # 🌍 commit state
    overwrite_judgment(new_judgment)

    return new_judgment
