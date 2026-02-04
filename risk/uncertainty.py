import math


class UncertaintySizer:
    """
    Position sizing based on uncertainty
    """

    def size(self, decision, volatility, max_size=0.05):
        if volatility <= 0:
            return 0.0

        uncertainty = math.log(1 + volatility)
        raw_size = decision.confidence / uncertainty

        return min(raw_size, max_size)
