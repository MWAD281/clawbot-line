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
    """
    outcome = normalize_outcome(raw_outcome)
    judgment = get_judgment()

    evolve_agents(judgment, outcome)

    return {
        "status": "EVOLUTION_COMPLETE",
        "outcome": outcome
    }
