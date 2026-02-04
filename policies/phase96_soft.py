from clawbot.decision import Decision
from clawbot.sizing.position import PositionSizer
from clawbot.analysis.regime import RegimeClassifier
from clawbot.analysis.regime_memory import RegimeMemory
from clawbot.evaluation.metrics import Metrics


class Phase96SoftPolicy:
    def __init__(self):
        self.name = "phase96_soft"

        self.genome = {
            "trending": {
                "confidence_threshold": 0.6,
                "risk_level": 0.7,
                "sizing_strategy": "kelly",
            },
            "range": {
                "confidence_threshold": 0.75,
                "risk_level": 0.4,
                "sizing_strategy": "fixed",
            },
            "volatile": {
                "confidence_threshold": 0.85,
                "risk_level": 0.3,
                "sizing_strategy": "conservative",
            },
        }

        self.metrics = Metrics()
        self.sizer = PositionSizer()
        self.regime_classifier = RegimeClassifier()
        self.regime_memory = RegimeMemory()

    def decide(self, world):
        regime = self.regime_classifier.classify(world)
        self.regime_memory.record(regime.name)

        g = self.genome[regime.name]
        confidence = abs(world.signal_strength())

        if confidence < g["confidence_threshold"]:
            d = Decision.no_trade("low_confidence", confidence)
            self.metrics.record(d)
            return d

        self.risk_level = g["risk_level"]
        self.sizing_strategy = g["sizing_strategy"]

        size = self.sizer.size(
            policy=self,
            regime=regime,
            confidence=confidence,
        )

        d = Decision.trade(
            side="buy" if world.signal_strength() > 0 else "sell",
            size=size,
            confidence=confidence,
            meta={
                "regime": regime.name,
                "transition_risk": self.regime_memory.transition_score(regime.name),
            },
        )

        self.metrics.record(d)
        return d
