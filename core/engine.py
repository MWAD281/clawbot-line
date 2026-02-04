import time
from clawbot.core.safety import Safety


class Engine:
    def __init__(
        self,
        policy,
        adapter,
        executor,
        clock=time,
        override_threshold=0.7
    ):
        self.policy = policy
        self.adapter = adapter
        self.executor = executor
        self.clock = clock
        self.override_threshold = override_threshold
        self.cycle = 0

    def run_once(self):
        self.cycle += 1

        world = {
            "timestamp": self.clock.time(),
            "cycle": self.cycle,
        }

        decision = self.policy.decide(world)
        decision = Safety.enforce(decision)

        if decision.confidence >= self.override_threshold:
            print("[ENGINE] executing engine decision")
            return self.executor.execute(decision, world)

        print("[ENGINE] fallback to legacy")
        legacy_decision = self.adapter.execute(world)
        return self.executor.execute(legacy_decision, world)

    def run_forever(self, interval_sec=60):
        while True:
            result = self.run_once()
            print(f"[ENGINE] cycle={self.cycle} result={result}")
            time.sleep(interval_sec)
