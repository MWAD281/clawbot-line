from clawbot.policies.base import Policy
from clawbot.core.decision import Decision


class Phase96SoftPolicy(Policy):
    def decide(self, world):
        return Decision(
            action="HOLD",
            confidence=0.42,
            reason="phase96_soft_run",
        )
