# market/market_feed.py
# Phase 12.6 – Real Market Feed Adapter (Safe / Extensible)

import time
import random
from typing import Dict

# -------------------------
# CONFIG
# -------------------------

CACHE_TTL = 30  # วินาที
_last_fetch = {}
_cache = {}


# -------------------------
# CORE FETCHER
# -------------------------

def _mock_price(base: float, vol: float = 0.01) -> float:
    """
    ใช้ตอนยังไม่ต่อ API จริง
    """
    drift = random.uniform(-vol, vol)
    return round(base * (1 + drift), 2)


def _fetch_market(symbol: str) -> Dict:
    """
    🔥 ตรงนี้คือจุดเปลี่ยนโลก
    ตอนนี้เป็น mock
    อนาคต → Binance / AlphaVantage / FRED / CME
    """
    if symbol == "BTC":
        price = _mock_price(43000, 0.02)
    elif symbol == "GOLD":
        price = _mock_price(2030, 0.005)
    elif symbol == "SPX":
        price = _mock_price(4800, 0.003)
    elif symbol == "USDTHB":
        price = _mock_price(35.5, 0.002)
    else:
        price = _mock_price(100, 0.01)

    return {
        "symbol": symbol,
        "price": price,
        "timestamp": time.time()
    }


# -------------------------
# PUBLIC API
# -------------------------

def get_market(symbol: str) -> Dict:
    """
    ใช้ cache กันระบบพัง / rate limit
    """
    now = time.time()

    if symbol in _cache:
        if now - _last_fetch.get(symbol, 0) < CACHE_TTL:
            return _cache[symbol]

    data = _fetch_market(symbol)
    _cache[symbol] = data
    _last_fetch[symbol] = now
    return data


def market_snapshot() -> Dict:
    """
    Snapshot ภาพโลกแบบ CEO มอง
    """
    symbols = ["BTC", "GOLD", "SPX", "USDTHB"]
    snap = {}

    for s in symbols:
        snap[s] = get_market(s)

    return snap


# -------------------------
# DEBUG
# -------------------------

def _debug_print():
    snap = market_snapshot()
    for k, v in snap.items():
        print(f"{k}: {v['price']} @ {time.ctime(v['timestamp'])}")
