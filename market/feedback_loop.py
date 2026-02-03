# market/feedback_loop.py
"""
Phase 12.8
Autonomous Feedback Loop
Market → Outcome → Judgment → Memory
"""

from typing import Dict
from market.outcome_translator import translate_market_to_outcome
from memory.judgment_state import get_judgment, overwrite_judgment
from evolution.judgment_evolver import evolve_judgment


def run_market_feedback_loop(market_state: Dict) -> Dict:
    """
    Loop หลักสำหรับให้ ClawBot เรียนรู้จากโลกจริง
    - ไม่เรียก AI
    - ไม่กระทบ webhook
    - ใช้ Darwinism เต็มรูป
    """

    # -------------------------
    # 1. Load current judgment
    # -------------------------
    judgment = get_judgment()
    if not isinstance(judgment, dict):
        judgment = {}

    # -------------------------
    # 2. Translate market → outcome
    # -------------------------
    outcome = translate_market_to_outcome(market_state)

    # -------------------------
    # 3. Evolve judgment
    # -------------------------
    new_judgment = evolve_judgment(judgment, outcome)

    # -------------------------
    # 4. Attach memory trace
    # -------------------------
    history = new_judgment.get("history", [])
    history.append({
        "source": "MARKET_FEEDBACK",
        "market_state": market_state,
        "outcome": outcome
    })

    # จำกัด memory ไม่ให้บวม
    new_judgment["history"] = history[-30:]

    # -------------------------
    # 5. Commit new state
    # -------------------------
    overwrite_judgment(new_judgment)

    return {
        "status": "FEEDBACK_APPLIED",
        "outcome": outcome,
        "judgment": new_judgment
    }
