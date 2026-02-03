"""
Clawbot Phase-96 Worker
SAFE PRODUCTION MODE
Logic X: Passive Heartbeat + Self-Health Guard
"""

import time
import os
import sys
import traceback
from datetime import datetime

SERVICE_NAME = "clawbot-phase-96-worker"
SLEEP_SECONDS = 30

def log(msg: str):
    print(f"[{SERVICE_NAME}] {msg}", flush=True)

# ===== LOGIC X (SAFE, READ-ONLY) =====
def logic_x():
    """
    SAFE LOGIC X
    - No external API
    - No DB
    - No mutation
    - Only observability
    """
    now = datetime.utcnow().isoformat()
    pid = os.getpid()
    env = os.getenv("ENV", "production")

    log(f"LOGIC_X_OK | time={now} | pid={pid} | env={env}")
# ====================================

def main():
    log("BOOT")
    log(f"Python={sys.version}")

    while True:
        try:
            logic_x()
            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            log("ERROR_CAUGHT")
            log(str(e))
            traceback.print_exc()
            time.sleep(5)  # anti-crash loop

if __name__ == "__main__":
    main()
