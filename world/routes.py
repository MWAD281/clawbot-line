# world/routes.py

from fastapi import APIRouter
from evolution.agent_evolver import evolve_agents
from memory.judgment_state import get_judgment
from world.normalize import normalize_outcome

router = APIRouter()


@router.get("/")
def world_state():
    """
    ดู world state ปัจจุบัน
    """
    return get_judgment()


@router.post("/world/evolve")
def weekly_evolve(raw_input: dict):
    """
    รับ input จากโลก (text หรือ outcome)
    """

    # 🧠 ถ้ามี text → แปลงเป็น outcome แบบ heuristic ชั่วคราว
    if "text" in raw_input:
        text = raw_input["text"]

        outcome = {
            "score": -0.6 if "เสี่ยง" in text else 0.2,
            "global_risk": 0.8 if ("สงคราม" in text or "ดอกเบี้ย" in text) else 0.4
        }
    else:
        # กรณีส่ง outcome มาโดยตรง
        outcome = normalize_outcome(raw_input)

    judgment = get_judgment()
    evolve_agents(judgment, outcome)

    return {
        "status": "EVOLUTION_COMPLETE",
        "input": raw_input,
        "outcome": outcome,
        "worldview": judgment.get("worldview"),
        "confidence": judgment.get("confidence")
    }
