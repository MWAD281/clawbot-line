# world/routes.py

from fastapi import APIRouter
from evolution.agent_evolver import evolve_agents
from memory.judgment_state import get_judgment

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

    # 🧠 ถ้ามี text → สร้าง outcome แบบ heuristic
    if "text" in raw_input:
        text = raw_input["text"]

        outcome = {
            "score": -0.6 if "เสี่ยง" in text else 0.2,
            "global_risk": 0.8 if ("สงคราม" in text or "ดอกเบี้ย" in text) else 0.4
        }
    else:
        # fallback ถ้าส่ง outcome มาเอง
        outcome = {
            "score": float(raw_input.get("score", 0.0)),
            "global_risk": float(raw_input.get("global_risk", 0.5))
        }

    judgment = get_judgment()
    evolve_agents(judgment, outcome)

    return {
        "status": "EVOLUTION_COMPLETE",
        "input": raw_input,
        "outcome": outcome,
        "worldview": judgment.get("worldview"),
        "confidence": judgment.get("confidence")
    }
