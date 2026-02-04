class RegulationRule:
    def __init__(self, name, allowed, max_leverage=None):
        self.name = name
        self.allowed = allowed
        self.max_leverage = max_leverage
