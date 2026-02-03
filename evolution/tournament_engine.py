# evolution/tournament_engine.py
# 🧬 Phase 12.3 – Multi-CEO Tournament (Darwin Arena)

import random
import time
from typing import List, Dict

from evolution.capital_allocator import (
    spawn_ceo,
    allocate_capital,
    is_alive,
    get_capital,
    leaderboard
)

from memory.agent_weights import increase_weight, decrease_weight, mute_agent


# -------------------------
# CONFIG
# -------------------------

LOSS_STREAK_KILL = 3
WIN_STREAK_BUFF = 3

# -------------------------
# STATE
# -------------------------

_ceo_stats: Dict[str, dict] = {}


def register_ceo(ceo_id: str):
    spawn_ceo(ceo_id)
    _ceo_stats[ceo_id] = {
        "win_streak": 0,
        "loss_streak": 0,
        "rounds": 0
    }


# -------------------------
# TOURNAMENT ROUND
# -------------------------

def run_tournament_round(
    ceo_ids: List[str],
    market_signal: str,
    market_volatility: float
) -> dict:
    """
    CEO ทุกตัวแข่งกันในรอบเดียว
    """

    round_result = {}

    for ceo_id in ceo_ids:
        if not is_alive(ceo_id):
            continue

        conviction = random.uniform(0.3, 0.9)

        result = allocate_capital(
            ceo_id=ceo_id,
            signal=market_signal,
            conviction=conviction,
            market_volatility=market_volatility
        )

        _ceo_stats[ceo_id]["rounds"] += 1

        if result.get("status") == "dead":
            mute_agent(ceo_id)
            round_result[ceo_id] = {
                "status": "dead",
                "capital": result.get("capital")
            }
            continue

        pnl = result.get("pnl", 0)

        # -------------------------
        # UPDATE STREAK
        # -------------------------

        if pnl > 0:
            _ceo_stats[ceo_id]["win_streak"] += 1
            _ceo_stats[ceo_id]["loss_streak"] = 0
        else:
            _ceo_stats[ceo_id]["loss_streak"] += 1
            _ceo_stats[ceo_id]["win_streak"] = 0

        # -------------------------
        # DARWIN RULES
        # -------------------------

        if _ceo_stats[ceo_id]["loss_streak"] >= LOSS_STREAK_KILL:
            mute_agent(ceo_id)
            round_result[ceo_id] = {
                "status": "killed_by_losses",
                "capital": get_capital(ceo_id)
            }
            continue

        if _ceo_stats[ceo_id]["win_streak"] >= WIN_STREAK_BUFF:
            increase_weight(ceo_id, amount=0.1)
            _ceo_stats[ceo_id]["win_streak"] = 0

        else:
            decrease_weight(ceo_id, amount=0.02)

        round_result[ceo_id] = {
            "status": "alive",
            "capital": get_capital(ceo_id),
            "pnl": pnl
        }

    return {
        "round": int(time.time()),
        "results": round_result,
        "leaderboard": leaderboard()
    }


# -------------------------
# SNAPSHOT
# -------------------------

def tournament_snapshot():
    return {
        cid: {
            "capital": get_capital(cid),
            "alive": is_alive(cid),
            **stats
        }
        for cid, stats in _ceo_stats.items()
    }
