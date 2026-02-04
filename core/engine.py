import time
from clawbot.core.safety import Safety


class Engine:
    def __init__(
        self,
        population,
        adapter,
        executor,
        judge,
        clock=time,
        override_threshold=0.7,
        darwin_cycle=10,
    ):
        self.population = population
        self.adapter = adapter
        self.executor = executor
        self.judge = judge
        self.clock = clock
        self.override_threshold = override_threshold
        self.cycle = 0
        self.darwin_cycle = darwin_cycle

    def run_once(self):
        self.cycle += 1

        world = {
            "timestamp": self.clock.time(),
            "cycle": self.cycle,
        }

        for policy in list(self.population.policies):
            decision = policy.decide(world)
            decision = Safety.enforce(decision)

            if decision.confidence >= self.override_threshold:
                execution = self.executor.execute(decision, world)
            else:
                legacy_decision = self.adapter.execute(world)
                execution = self.executor.execute(legacy_decision, world)
                decision = legacy_decision

            score, reason = self.judge.evaluate(decision, execution)
            policy.metrics.record(score)

        # === Phase F+ Darwinism ===
        if self.cycle % self.darwin_cycle == 0:
            print(f"\n🧬 DARWIN EVOLUTION @ cycle {self.cycle}")
            self.population.evolve()

        return {
            "cycle": self.cycle,
            "population": self.population.snapshot(),
        }

    def run_forever(self, interval_sec=60):
        print("🚀 Engine started | Darwinism ACTIVE")
        while True:
            result = self.run_once()
            print(result)
            time.sleep(interval_sec)
