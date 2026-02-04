from clawbot.infra.logger import get_logger
from clawbot.infra.clock import Clock
from clawbot.core.world import World
from clawbot.core.safety import Safety
from clawbot.evaluation.judge import judge

class Engine:
    def __init__(self, policy, interval_sec: int = 60):
        self.policy = policy
        self.clock = Clock()
        self.world = World()
        self.interval = interval_sec
        self.logger = get_logger("PHASE96")

    def run_once(self, cycle: int):
        world_state = self.world.snapshot()
        decision = self.policy.decide(world_state)

        if Safety.allow(decision):
            scores = judge(decision)
            self.logger.info(
                f"| cycle={cycle} | decision={decision.action} "
                f"| confidence={decision.confidence} "
                f"| scores={scores}"
            )

    def run_forever(self):
        cycle = 1
        self.logger.info("PHASE96 | STARTED | mode=SOFT_RUN_SAFE")
        while True:
            self.run_once(cycle)
            cycle += 1
            self.clock.sleep(self.interval)
