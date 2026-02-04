from clawbot.policies.base import Policy
from clawbot.core.decision import Decision

class Phase96SoftPolicy(Policy):

    def decide(self, world_state: dict) -> Decision:
        return Decision(
            action="NO_OP",
            confidence=0.01,
            reason="Phase96 SOFT_RUN observation only",
            meta={"world": world_state}
        )
