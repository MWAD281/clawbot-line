"""
Clawbot Phase-96 Worker
SAFE PRODUCTION MODE
- No side effects on import
- No auto-run AI
- No network calls at startup
"""

import time
import os
import sys
import traceback

SERVICE_NAME = "clawbot-phase-96-worker"

def boot_log(msg: str):
    print(f"[{SERVICE_NAME}] {msg}", flush=True)

def main_loop():
    boot_log("MAIN LOOP STARTED")

    while True:
        try:
            # ---- HEARTBEAT ONLY (SAFE) ----
            boot_log("Worker alive")

            # TODO:
            # - Put REAL logic here later
            # - Queue polling
            # - Cron-like task
            # - AI execution step

            time.sleep(30)

        except Exception as e:
            boot_log("ERROR in main loop")
            boot_log(str(e))
            traceback.print_exc()
            time.sleep(5)  # prevent crash loop


if __name__ == "__main__":
    boot_log("BOOT OK")
    boot_log(f"Python: {sys.version}")
    boot_log(f"PID: {os.getpid()}")

    main_loop()
