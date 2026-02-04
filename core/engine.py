# clawbot/core/engine.py

from infra.logger import log
from infra.clock import now
from core.decision import Decision

class Engine:
    def __init__(self, policy, mode="SOFT_RUN_SAFE"):
        self.policy = policy
        self.mode = mode
        self.cycle = 0

    def step(self, world):
        self.cycle += 1

        decision = self.policy.decide(world)

        log({
            "phase": self.policy.phase,
            "cycle": self.cycle,
            "decision": decision.to_dict(),
            "mode": self.mode,
            "ts": now()
        })

        # Phase B: ยังไม่ execute action จริง
        return decision
