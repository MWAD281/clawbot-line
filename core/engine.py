import time
from clawbot.core.safety import Safety
from clawbot.core.decision import Decision


class Engine:
    def __init__(
        self,
        policy,
        adapter,
        clock=time,
        override_threshold=0.7
    ):
        self.policy = policy
        self.adapter = adapter
        self.clock = clock
        self.override_threshold = override_threshold
        self.cycle = 0

    def run_once(self):
        self.cycle += 1

        world = {
            "timestamp": self.clock.time(),
            "cycle": self.cycle,
        }

        engine_decision = self.policy.decide(world)
        engine_decision = Safety.enforce(engine_decision)

        # 🔁 Phase C logic
        if engine_decision.action == "OVERRIDE":
            if engine_decision.confidence >= self.override_threshold:
                print("[ENGINE] OVERRIDE decision applied")
                return engine_decision
            else:
                print("[ENGINE] override confidence too low → fallback legacy")

        # fallback to legacy
        legacy_decision = self.adapter.execute(world)
        return legacy_decision

    def run_forever(self, interval_sec=60):
        while True:
            result = self.run_once()
            print(f"[ENGINE] cycle={self.cycle} result={result}")
            time.sleep(interval_sec)
