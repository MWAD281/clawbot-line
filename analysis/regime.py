class MarketRegime:
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def __repr__(self):
        return f"<Regime {self.name} ({self.score:.2f})>"


class RegimeClassifier:
    """
    VERY SAFE heuristic classifier
    Replace with ML later without touching policy code
    """

    def classify(self, world):
        vol = world.volatility()
        trend = world.trend_strength()

        if vol > 0.7:
            return MarketRegime("volatile", vol)

        if trend > 0.6:
            return MarketRegime("trending", trend)

        return MarketRegime("range", 1 - abs(trend))
