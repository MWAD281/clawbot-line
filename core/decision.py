# clawbot/core/decision.py

class Decision:
    def __init__(self, action, confidence=0.0, reason=""):
        self.action = action
        self.confidence = confidence
        self.reason = reason

    def to_dict(self):
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reason": self.reason
        }
