from clawbot.core.decision import Decision


class Phase96SoftPolicy:
    def decide(self, world):
        cycle = world["cycle"]

        # ทุก 10 cycle → ลอง trade
        if cycle % 10 == 0:
            return Decision(
                action="TRADE",
                confidence=0.85,
                reason="phase96_engine_trade_test"
            )

        return Decision(
            action="NO_TRADE",
            confidence=0.95,
            reason="wait_and_observe"
        )
