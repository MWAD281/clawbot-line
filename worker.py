# worker.py
# SAFE PRODUCTION WORKER (Logic X)
# ไม่มี dependency ภายนอก
# ไม่เรียก evolution / phase / strategy ใดๆ
# ใช้แค่ heartbeat เพื่อให้ Render worker อยู่รอด

import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

SERVICE_NAME = "clawbot-phase-96-worker"
MODE = os.getenv("WORKER_MODE", "SAFE")

def heartbeat():
    logging.info(
        f"[{SERVICE_NAME}] LOGIC_X_OK | mode={MODE}"
    )

if __name__ == "__main__":
    logging.info(f"[{SERVICE_NAME}] STARTED")
    while True:
        heartbeat()
        time.sleep(30)
