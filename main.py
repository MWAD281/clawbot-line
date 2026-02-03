import os
import random
import time
from market.market_probe import get_market_snapshot
from evolution.strategy_pool import load_strategies, kill_strategy, mutate_strategy
from memory.performance_log import log_performance

PHASE = 96
MODE = "sandbox"  # เปลี่ยนเป็น "live" ตอน Phase 97

CAPITAL = 1000  # virtual capital
MAX_RISK_PER_TRADE = 0.01
CYCLE_PER_RUN = 50


def simulate_trade(strategy, market):
    """
    จำลองผลลัพธ์การเทรด (ไม่ยิง order จริง)
    """
    edge = strategy["edge"]
    volatility = market["volatility"]

    win = random.random() < edge
    pnl = (
        random.uniform(0.5, 1.5) * volatility
        if win else
        -random.uniform(0.5, 1.2) * volatility
    )
    return pnl


def run_phase_96():
    print("🔥 Phase 96: Strategy Survival Ranking")

    strategies = load_strategies()
    market = get_market_snapshot()

    for cycle in range(CYCLE_PER_RUN):
        print(f"\n--- Cycle {cycle + 1}/{CYCLE_PER_RUN} ---")

        for s in strategies[:]:
            pnl = simulate_trade(s, market)
            s["capital"] += pnl
            log_performance(s["id"], pnl)

            if s["capital"] <= CAPITAL * 0.7:
                print(f"☠️ Strategy {s['id']} died")
                kill_strategy(s["id"])
                strategies.remove(s)

        # Mutate ถ้ากลยุทธ์เริ่มน้อย
        if len(strategies) < 5:
            print("🧬 Mutating new strategies")
            strategies.extend(mutate_strategy())

        time.sleep(0.2)

    print("\n✅ Phase 96 Complete")
    print("Survivors:", [s["id"] for s in strategies])


if __name__ == "__main__":
    run_phase_96()
