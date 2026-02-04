import time
from clawbot.core.safety import Safety


class Engine:
    def __init__(self, policy, adapter, clock=time):
        self.policy = policy
        self.adapter = adapter
        self.clock = clock
        self.cycle = 0

    def run_once(self):
        self.cycle += 1

        world = {
            "timestamp": self.clock.time(),
            "cycle": self.cycle,
        }

        decision = self.policy.decide(world)

        # ครอบความปลอดภัย
        decision = Safety.enforce(decision)

        # Phase B = delegate ทุกอย่าง
        if decision.action == "DELEGATE_LEGACY":
            return self.adapter.execute(world)

        return decision

    def run_forever(self, interval_sec=60):
        while True:
            result = self.run_once()
            print(f"[ENGINE] cycle={self.cycle} result={result}")
            time.sleep(interval_sec)
