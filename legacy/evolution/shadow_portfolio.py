# evolution/shadow_portfolio.py
# 🧬 Phase 12.4 – Shadow Portfolio Engine

import time
from typing import Dict

from memory.agent_weights import get_weight
from evolution.capital_allocator import is_alive
from memory.judgment_state import overwrite_judgment


# -------------------------
# CONFIG
# -------------------------

DEFAULT_START_CAPITAL = 100_000  # เงินจำลอง
MAX_POSITION_PCT = 0.3           # max 30% ต่อ asset


# -------------------------
# STATE
# -------------------------

_shadow_portfolios: Dict[str, dict] = {}


# -------------------------
# INIT
# -------------------------

def init_shadow_portfolio(ceo_id: str):
    if ceo_id not in _shadow_portfolios:
        _shadow_portfolios[ceo_id] = {
            "capital": DEFAULT_START_CAPITAL,
            "positions": {},  # asset -> qty
            "history": [],
            "created_at": time.time()
        }


# -------------------------
# PRICE FEED (stub)
# -------------------------

def get_market_price(asset: str) -> float:
    """
    🔌 Phase 12.4 ใช้ mock / manual price
    Phase 12.6 จะเสียบ API จริง
    """
    mock_prices = {
        "BTC": 43000,
        "ETH": 2300,
        "GOLD": 2050,
        "SPX": 4950
    }
    return mock_prices.get(asset.upper(), 100)


# -------------------------
# TRADE SIMULATION
# -------------------------

def simulate_trade(
    ceo_id: str,
    asset: str,
    direction: str,
    conviction: float
):
    if not is_alive(ceo_id):
        return {"status": "dead"}

    init_shadow_portfolio(ceo_id)

    portfolio = _shadow_portfolios[ceo_id]
    price = get_market_price(asset)

    weight = get_weight(ceo_id)
    position_size = (
        portfolio["capital"]
        * min(MAX_POSITION_PCT, conviction)
        * weight
    )

    qty = position_size / price

    if direction == "buy":
        portfolio["positions"][asset] = (
            portfolio["positions"].get(asset, 0) + qty
        )
        portfolio["capital"] -= position_size

    elif direction == "sell":
        held = portfolio["positions"].get(asset, 0)
        sell_qty = min(held, qty)
        portfolio["positions"][asset] = held - sell_qty
        portfolio["capital"] += sell_qty * price

    portfolio["history"].append({
        "ts": time.time(),
        "asset": asset,
        "direction": direction,
        "price": price,
        "qty": qty,
        "capital": portfolio["capital"]
    })

    return {
        "status": "ok",
        "capital": portfolio["capital"]
    }


# -------------------------
# VALUATION
# -------------------------

def portfolio_value(ceo_id: str) -> float:
    if ceo_id not in _shadow_portfolios:
        return 0

    portfolio = _shadow_portfolios[ceo_id]
    value = portfolio["capital"]

    for asset, qty in portfolio["positions"].items():
        value += qty * get_market_price(asset)

    return value


# -------------------------
# SNAPSHOT
# -------------------------

def shadow_snapshot():
    snap = {}

    for ceo_id, p in _shadow_portfolios.items():
        snap[ceo_id] = {
            "value": portfolio_value(ceo_id),
            "capital": p["capital"],
            "positions": p["positions"]
        }

    return snap


# -------------------------
# FEEDBACK → WORLDVIEW
# -------------------------

def feed_shadow_result_to_world():
    """
    เอาผลพอร์ตเงาไปรวมเป็น judgment โลก
    """
    values = [
        portfolio_value(cid)
        for cid in _shadow_portfolios
        if is_alive(cid)
    ]

    if not values:
        return

    avg = sum(values) / len(values)

    if avg > DEFAULT_START_CAPITAL * 1.05:
        overwrite_judgment({
            "global_risk": "RISK_ON",
            "worldview": "OPPORTUNITY_DOMINANT",
            "stance": "AGGRESSIVE"
        })
    elif avg < DEFAULT_START_CAPITAL * 0.95:
        overwrite_judgment({
            "global_risk": "RISK_OFF",
            "worldview": "CAPITAL_PRESERVATION",
            "stance": "DEFENSIVE"
        })
