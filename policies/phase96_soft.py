import random
from clawbot.core.decision import Decision
from clawbot.evaluation.metrics import Metrics


class Phase96SoftPolicy:
    def __init__(self):
        self.name = "phase96_soft"
        self.confidence_bias = 0.5
        self.metrics = Metrics()

    def decide(self, world):
        confidence = min(0.95, max(0.05, random.random() + self.confidence_bias - 0.5))

        action = "TRADE" if confidence > 0.6 else "NO_TRADE"

        return Decision(
            action=action,
            confidence=confidence,
            reason="phase96_soft_policy",
        )
