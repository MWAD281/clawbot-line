# world/routes.py

from fastapi import APIRouter
from memory.judgment_state import get_judgment
from evolution.agent_evolver import evolve_agents
from world.outcome_schema import normalize_outcome

router = APIRouter()


@router.post("/world/evolve")
def weekly_evolve(raw_outcome: dict):
    """
    เรียกสัปดาห์ละครั้ง / หลังเหตุการณ์ใหญ่
    เพื่อให้ระบบ AI ปรับตัว (Evolution Trigger)
    """

    # 1️⃣ Normalize outcome จาก council / world
    outcome = normalize_outcome(raw_outcome)

    # 2️⃣ 🔁 OPTION A: map API schema -> internal schema
    # เพื่อให้ memory / evolver ใช้ key เดียวกัน
    outcome["global_risk"] = outcome.pop("risk")

    # 3️⃣ ดึง judgment ปัจจุบันของโลก
    judgment = get_judgment()

    # 4️⃣ ให้ agent ทั้งระบบ evolve ตามผลลัพธ์
    evolve_agents(judgment, outcome)

    # 5️⃣ ส่งผลลัพธ์กลับ
    return {
        "status": "EVOLUTION_COMPLETE",
        "outcome": outcome
    }
