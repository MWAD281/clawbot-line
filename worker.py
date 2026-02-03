# worker.py
import time
import logging

logging.basicConfig(level=logging.INFO)

def main_loop():
    logging.info("ClawBot worker started")

    while True:
        # placeholder logic
        logging.info("Worker heartbeat: alive")
        time.sleep(30)

if __name__ == "__main__":
    main_loop()
