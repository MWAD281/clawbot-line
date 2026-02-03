import random
import time


def get_market_snapshot():
    """
    Mock market data สำหรับ Phase 96 (Sandbox / Simulation)
    """
    return {
        "timestamp": time.time(),
        "volatility": random.uniform(0.5, 2.0),
        "trend": random.choice(["up", "down", "sideways"]),
        "liquidity": random.uniform(0.3, 1.0),
    }
