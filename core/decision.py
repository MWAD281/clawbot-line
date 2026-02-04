# clawbot/core/decision.py

class Decision:
    def __init__(self, action, confidence=0.0, reason=None, meta=None):
        self.action = action
        self.confidence = confidence
        self.reason = reason or ""
        self.meta = meta or {}

    def to_dict(self):
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reason": self.reason,
            "meta": self.meta,
        }
