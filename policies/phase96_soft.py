from clawbot.core.decision import Decision
import random


class Phase96SoftPolicy:
    def decide(self, world):
        cycle = world["cycle"]

        # Phase C: ทดลอง override เป็นช่วง ๆ
        if cycle % 10 == 0:
            return Decision(
                action="OVERRIDE",
                confidence=0.8,
                reason="engine_override_test"
            )

        return Decision(
            action="DELEGATE_LEGACY",
            confidence=0.99,
            reason="safe_delegate"
        )
