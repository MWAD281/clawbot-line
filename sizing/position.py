class PositionSizer:
    """
    Convert policy traits + regime → position size (0.0 - 1.0)
    SAFE: never exceed max_risk
    """

    def __init__(self, max_risk=0.03):
        self.max_risk = max_risk

    def size(self, policy, regime, confidence):
        """
        confidence: decision confidence (0-1)
        regime: MarketRegime object
        """

        base = confidence * policy.risk_level

        # regime adjustment
        if regime.name == "volatile":
            base *= 0.5
        elif regime.name == "trending":
            base *= 1.2
        elif regime.name == "range":
            base *= 0.8

        # timing bias
        if policy.timing_bias == -1:
            base *= 0.8
        elif policy.timing_bias == 1:
            base *= 1.1

        # clamp
        return max(0.0, min(base, self.max_risk))
