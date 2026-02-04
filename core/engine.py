import time
from clawbot.core.safety import Safety


class Engine:
    def __init__(
        self,
        policy,
        adapter,
        executor,
        judge,
        metrics,
        clock=time,
        override_threshold=0.7
    ):
        self.policy = policy
        self.adapter = adapter
        self.executor = executor
        self.judge = judge
        self.metrics = metrics
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
            execution = self.executor.execute(decision, world)
        else:
            legacy_decision = self.adapter.execute(world)
            execution = self.executor.execute(legacy_decision, world)
            decision = legacy_decision

        score, reason = self.judge.evaluate(decision, execution)
        self.metrics.record(score)

        return {
            "decision": repr(decision),
            "execution": execution,
            "score": score,
            "judge_reason": reason,
            "metrics": self.metrics.snapshot(),
        }

    def run_forever(self, interval_sec=60):
        while True:
            result = self.run_once()
            print(f"[ENGINE] {result}")
            time.sleep(interval_sec)
