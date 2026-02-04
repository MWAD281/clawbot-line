from clawbot.policies.phase96_soft import decide
from clawbot.core.safety import soft_guard
from clawbot.infra.logger import log

class Engine:
    def __init__(self, mode="SOFT_RUN_SAFE"):
        self.mode = mode
        self.cycle = 0

    def step(self, market_snapshot: dict):
        self.cycle += 1

        decision = decide(market_snapshot)
        decision = soft_guard(decision)

        log("PHASE96", {
            "cycle": self.cycle,
            "decision": {
                "action": decision.action,
                "confidence": round(decision.confidence, 3),
                "reason": decision.reason
            }
        })

        return decision
