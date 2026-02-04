from clawbot.decision import Decision
from clawbot.sizing.position import PositionSizer
from clawbot.analysis.regime import RegimeClassifier
from clawbot.evaluation.metrics import Metrics


class Phase96SoftPolicy:
    def __init__(self):
        self.name = "phase96_soft"

        # === REGIME GENOMES ===
        self.genome = {
            "trending": {
                "confidence_threshold": 0.6,
                "risk_level": 0.7,
                "timing_bias": 1,
                "sizing_strategy": "kelly",
            },
            "range": {
                "confidence_threshold": 0.75,
                "risk_level": 0.4,
                "timing_bias": 0,
                "sizing_strategy": "fixed",
            },
            "volatile": {
                "confidence_threshold": 0.85,
                "risk_level": 0.3,
                "timing_bias": -1,
                "sizing_strategy": "conservative",
            },
        }

        self.metrics = Metrics()
        self.sizer = PositionSizer()
        self.regime_classifier = RegimeClassifier()

    def decide(self, world):
        regime = self.regime_classifier.classify(world)
        g = self.genome[regime.name]

        signal = world.signal_strength()
        confidence = abs(signal)

        if confidence < g["confidence_threshold"]:
            decision = Decision.no_trade(
                reason="low_confidence",
                confidence=confidence,
            )
            self.metrics.record(decision)
            return decision

        # attach traits dynamically
        self.risk_level = g["risk_level"]
        self.timing_bias = g["timing_bias"]
        self.sizing_strategy = g["sizing_strategy"]

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
                "genome": g,
            },
        )

        self.metrics.record(decision)
        return decision
