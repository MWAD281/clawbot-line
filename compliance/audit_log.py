# clawbot/compliance/audit_log.py

import json
import time


class AuditLog:
    """
    Immutable audit log
    """

    def __init__(self):
        self.records = []

    def record(self, event: dict):
        event["timestamp"] = time.time()
        self.records.append(event)

    def export(self) -> str:
        return json.dumps(self.records, indent=2)
