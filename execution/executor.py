from clawbot.execution.simulator import TradeSimulator


class Executor:
    def __init__(self, mode="SOFT_RUN_SAFE"):
        self.mode = mode
        self.simulator = TradeSimulator()

    def execute(self, decision, world):
        if decision.action == "TRADE":
            if self.mode == "SOFT_RUN_SAFE":
                return self.simulator.execute(decision, world)

        if decision.action == "NO_TRADE":
            return {
                "status": "NO_TRADE",
                "reason": decision.reason,
                "cycle": world["cycle"]
            }

        return {
            "status": "IGNORED",
            "action": decision.action
        }
