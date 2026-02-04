from clawbot.core.decision import Decision


class SafetyLayer:
    def apply(self, decision: Decision) -> Decision:
        # HARD GUARD
        if decision.confidence < 0.5:
            return Decision(
                action="HOLD",
                confidence=decision.confidence,
                reason="safety_override_low_confidence",
                risk=0.0,
            )

        return decision
