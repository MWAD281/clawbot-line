import random
import time
from world.market_probe import get_market_snapshot

CAPITAL = 1000
CYCLE_PER_RUN = 50

def simulate_trade(strategy, market):
    win = random.random() < strategy["edge"]
    pnl = random.uniform(-1, 1) * market["volatility"]
    return pnl if win else -abs(pnl)

def run_phase_96():
    print("🔥 Phase 96: Strategy Survival Ranking")

    strategies = [
        {"id": f"s{i}", "edge": random.uniform(0.45, 0.55), "capital": CAPITAL}
        for i in range(10)
    ]

    market = get_market_snapshot()

    for cycle in range(CYCLE_PER_RUN):
        for s in strategies[:]:
            pnl = simulate_trade(s, market)
            s["capital"] += pnl

            if s["capital"] < CAPITAL * 0.7:
                strategies.remove(s)

        time.sleep(0.1)

    print("✅ Survivors:", [s["id"] for s in strategies])
