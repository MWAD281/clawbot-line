import time
import sys
import traceback

print("ClawBot worker booting...")

try:
    while True:
        print("Worker alive - heartbeat")
        time.sleep(30)

except Exception as e:
    print("WORKER CRASHED")
    traceback.print_exc()
    sys.exit(1)
