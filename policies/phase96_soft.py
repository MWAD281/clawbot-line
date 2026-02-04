from clawbot.core.decision import Decision


class Phase96SoftPolicy:
    def decide(self, world):
        return Decision(
            action="DELEGATE_LEGACY",
            confidence=0.99,
            reason="phase96_soft_wrap"
        )
