# world/market_probe.py
import random
import time

def get_market_snapshot():
    return {
        "symbol": "BTCUSDT",
        "price": round(random.uniform(60000, 70000), 2),
        "volatility": round(random.uniform(0.5, 2.0), 2),
        "timestamp": int(time.time())
    }
