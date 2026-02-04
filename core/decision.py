class Decision:
    def __init__(self, action, confidence=0.0, reason=""):
        self.action = action
        self.confidence = confidence
        self.reason = reason

    def __repr__(self):
        return (
            f"Decision(action={self.action}, "
            f"confidence={self.confidence}, "
            f"reason={self.reason})"
        )
