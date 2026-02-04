from clawbot.decision import Decision
from clawbot.sizing.position import PositionSizer
from clawbot.analysis.regime import RegimeClassifier
from clawbot.evaluation.metrics import Metrics


class Phase96SoftPolicy:
    def __init__(self):
        self.name = "phase96_soft"

        # === GENETIC TRAITS ===
        self.confidence_threshold = 0.7
        self.risk_level = 0.5
        self.timing_bias = 0

        # === SYSTEM ===
        self.metrics = Metrics()
        self.sizer = PositionSizer()
        self.regime_classifier = RegimeClassifier()

    def decide(self, world):
        regime = self.regime_classifier.classify(world)

        signal = world.signal_strength()
        confidence = abs(signal)

        if confidence < self.confidence_threshold:
            decision = Decision.no_trade(
                reason="low_confidence",
                confidence=confidence,
            )
            self.metrics.record(decision)
            return decision

        size = self.sizer.size(
            policy=self,
            regime=regime,
            confidence=confidence,
        )

        decision = Decision.trade(
            side="buy" if signal > 0 else "sell",
            size=size,
            confidence=confidence,
            meta={
                "regime": regime.name,
                "traits": {
                    "risk": self.risk_level,
                    "timing": self.timing_bias,
                },
            },
        )

        self.metrics.record(decision)
        return decision
