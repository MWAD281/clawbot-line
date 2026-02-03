import time
import random
import logging

logging.basicConfig(level=logging.INFO)

# ===== Strategy =====

class Strategy:
    def __init__(self, name):
        self.name = name
        self.score = 0

    def run(self):
        # จำลอง performance
        self.score += random.uniform(-1, 2)
        return self.score


# ===== Darwin Pool =====

class StrategyPool:
    def __init__(self):
        self.strategies = [
            Strategy("alpha"),
            Strategy("beta"),
            Strategy("gamma"),
        ]

    def evolve(self):
        self.strategies.sort(key=lambda s: s.score, reverse=True)

        best = self.strategies[0]
        worst = self.strategies[-1]

        logging.info(f"BEST: {best.name} ({best.score:.2f})")
        logging.info(f"KILL: {worst.name} ({worst.score:.2f})")

        # Kill & mutate
        self.strategies.pop()
        self.strategies.append(
            Strategy(name=f"{best.name}_mutated")
        )


# ===== Worker Loop =====

def main():
    pool = StrategyPool()
    logging.info("🧬 ClawBot Darwin Worker started")

    while True:
        for s in pool.strategies:
            s.run()

        pool.evolve()

        logging.info("Worker heartbeat: alive")
        time.sleep(30)  # Render friendly


if __name__ == "__main__":
    main()
