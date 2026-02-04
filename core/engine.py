# clawbot/core/engine.py

from infra.logger import log
from infra.clock import now

class Engine:
    def __init__(self, policy, world):
        self.policy = policy
        self.world = world
        self.cycle = 0

    def step(self):
        self.cycle += 1

        market = self.world.observe()
        decision = self.policy.decide(market)

        log("ENGINE_STEP", {
            "cycle": self.cycle,
            "decision": decision.to_dict()
        })

        return decision
