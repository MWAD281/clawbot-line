# worker.py

import time
from evolution.strategy_pool import StrategyPool

def main():
    print("🔥 Phase 96 worker started")

    pool = StrategyPool(initial_size=5)

    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- Cycle {cycle} ---")

        pool.evaluate()
        pool.evolve()

        time.sleep(10)  # กัน CPU พัง

if __name__ == "__main__":
    main()
