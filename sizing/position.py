from clawbot.sizing.strategies import (
    FixedFractional,
    KellyLike,
    Conservative,
)


class PositionSizer:
    def __init__(self, max_risk=0.03):
        self.max_risk = max_risk
        self.strategies = {
            "fixed": FixedFractional(),
            "kelly": KellyLike(),
            "conservative": Conservative(),
        }

    def size(self, policy, regime, confidence):
        strat = self.strategies.get(
            policy.sizing_strategy, FixedFractional()
        )

        base = strat.size(confidence, policy.risk_level)

        # regime modifier
        if regime.name == "volatile":
            base *= 0.5
        elif regime.name == "trending":
            base *= 1.2

        return max(0.0, min(base, self.max_risk))
