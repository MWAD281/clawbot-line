class FixedFractional:
    def size(self, confidence, risk):
        return confidence * risk


class KellyLike:
    def size(self, confidence, risk):
        return (confidence ** 2) * risk


class Conservative:
    def size(self, confidence, risk):
        return min(confidence, 0.5) * risk * 0.7
