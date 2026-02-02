# evolution/judgment_evolver.py

from memory.judgment_state import get_judgment, overwrite_judgment


def evolve_judgment(judgment: dict, outcome: dict) -> dict:
    """
    ปรับ worldview ของระบบจาก outcome โลกจริง
    ใช้โดย agent_evolver / evolve_from_ai
    """

    if not isinstance(judgment, dict):
        return judgment

    if not isinstance(outcome, dict):
        return judgment

    score = outcome.get("score", 0)
    global_risk = outcome.get("global_risk", 0.5)

    # ค่า default (กันพัง)
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


# 🧬 Phase 9+ : evolve จากผล AI โดยตรง (LINE / OpenAI)
def evolve_from_ai(user_text: str, ai_result) -> dict:
    """
    evolve judgment จากผลลัพธ์ AI
    - ai_result ต้องเป็น dict (raw OpenAI response หรือ structured result)
    - ถ้าไม่ใช่ dict → ignore (ไม่พังระบบ)
    """

    # 🛡️ กันพังระดับระบบ
    if not isinstance(ai_result, dict):
        return get_judgment()

    # ดึง world state ปัจจุบัน
    judgment = get_judgment()

    # 🔎 พยายาม extract outcome จาก AI
    # (รองรับหลาย format ในอนาคต)
    outcome = {
        "score": ai_result.get("score", 0),
        "global_risk": ai_result.get("global_risk", 0.5)
    }

    new_judgment = evolve_judgment(judgment, outcome)

    # 🌍 commit state
    overwrite_judgment(new_judgment)

    return new_judgment
