# worker.py
# PHASE 96 - SAFE SOFT RUN (RENDER STABLE)
# ❌ no imports from project
# ❌ no side effects
# ✅ infinite alive worker
# ✅ log only

import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | PHASE96 | %(message)s",
)

SERVICE_NAME = "clawbot-phase-96-worker"
MODE = "SOFT_RUN_SAFE"

def soft_decision():
    return {
        "action": "HOLD",
        "confidence": 0.42,
        "reason": "phase96_soft_run_safe"
    }

if __name__ == "__main__":
    logging.info(f"{SERVICE_NAME} STARTED | mode={MODE}")

    cycle = 0

    while True:
        try:
            cycle += 1
            decision = soft_decision()

            logging.info({
                "cycle": cycle,
                "timestamp": datetime.utcnow().isoformat(),
                "decision": decision
            })

            time.sleep(60)  # เบาที่สุดสำหรับ Render
        except Exception as e:
            logging.error(f"SAFE ERROR (ignored): {e}")
            time.sleep(30)
