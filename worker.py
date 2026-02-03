import time
import logging
import random
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def main():
    logging.info("🧬 ClawBot Worker booted successfully")
    logging.info(f"Python version: {sys.version}")

    score = 0.0
    cycle = 0

    while True:
        cycle += 1
        delta = random.uniform(-1, 2)
        score += delta

        logging.info(
            f"Heartbeat #{cycle} | score={score:.2f} | delta={delta:.2f}"
        )

        # Render-friendly sleep
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("❌ Worker crashed")
        raise
