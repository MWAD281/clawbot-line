from clawbot.core.safety import SafetyLayer
from clawbot.infra.logger import log
from clawbot.core.world import WorldState
from clawbot.infra.clock import utcnow


class Engine:
    def __init__(self, policy):
        self.policy = policy
        self.safety = SafetyLayer()
        self.cycle = 0

    def run_once(self):
        self.cycle += 1

        world = WorldState(timestamp=utcnow())
        decision = self.policy.decide(world)
        decision = self.safety.apply(decision)

        log(
            "PHASE96",
            cycle=self.cycle,
            decision=decision.as_dict(),
        )

        return decision
