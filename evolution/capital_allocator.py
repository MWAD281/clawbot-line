# evolution/capital_allocator.py
# 💰 Phase 12.2 – Capital Allocation Simulation

import random
import time
from typing import Dict

from memory.ceo_memory import record_experience, compress_memory

# -------------------------
# CONFIG
# -------------------------

INITIAL_CAPITAL = 1_000_000  # เงินจำลอง
MAX_RISK_PER_TRADE = 0.2     # เสี่ยงสูงสุดต่อรอบ
DEATH_THRESHOLD = 0.3        # เงิน < 30% = ตาย

# -------------------------
# CEO CAPITAL STATE
# -------------------------

_ceo_capital: Dict[str, float] = {}
_ceo_alive: Dict[str, bool] = {}


def spawn_ceo(ceo_id: str):
    _ceo_capital[ceo_id] = INITIAL_CAPITAL
    _ceo_alive[ceo_id] = True


def is_alive(ceo_id: str) -> bool:
    return _ceo_alive.get(ceo_id, False)


def get_capital(ceo_id: str) -> float:
    return _ceo_capital.get(ceo_id, 0.0)


# -------------------------
# CORE SIMULATION
# -------------------------

def allocate_capital(
    ceo_id: str,
    signal: str,
    conviction: float,
    market_volatility: float
) -> dict:
    """
    CEO ตัดสินใจลงเงิน
    """

    if not is_alive(ceo_id):
        return {"status": "dead"}

    capital = _ceo_capital[ceo_id]

    risk = min(MAX_RISK_PER_TRADE, max(0.05, conviction))
    bet_size = capital * risk

    # ผลลัพธ์ตลาด (จำลอง)
    edge = conviction - market_volatility
    noise = random.uniform(-0.2, 0.2)

    pnl_ratio = edge + noise
    pnl = bet_size * pnl_ratio

    _ceo_capital[ceo_id] += pnl

    # -------------------------
    # EXPERIENCE RECORD
    # -------------------------

    score = pnl / max(1, bet_size)
    outcome = "profit" if pnl > 0 else "loss"

    record_experience(
        ceo_id=ceo_id,
        signal=signal,
        outcome=outcome,
        score=score
    )

    # compress memory occasionally
    if random.random() < 0.3:
        compress_memory(ceo_id)

    # -------------------------
    # DEATH CHECK
    # -------------------------

    if _ceo_capital[ceo_id] < INITIAL_CAPITAL * DEATH_THRESHOLD:
        _ceo_alive[ceo_id] = False
        return {
            "status": "dead",
            "capital": _ceo_capital[ceo_id]
        }

    return {
        "status": "alive",
        "capital": round(_ceo_capital[ceo_id], 2),
        "pnl": round(pnl, 2),
        "score": round(score, 3)
    }


# -------------------------
# LEADERBOARD
# -------------------------

def leaderboard(top_n: int = 5):
    alive = {
        cid: cap
        for cid, cap in _ceo_capital.items()
        if _ceo_alive.get(cid)
    }

    return sorted(
        alive.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
