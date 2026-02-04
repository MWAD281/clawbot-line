# clawbot/infra/logger.py

import json
import sys

def log(payload: dict):
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
