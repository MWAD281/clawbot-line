class CapitalScaler:
    """
    Increase capital only when policy proves stability
    """

    def __init__(self, max_step=1.3):
        self.max_step = max_step

    def scale(self, policy):
        metrics = policy.metrics

        if metrics.max_drawdown < 0.1 and metrics.stability > 0.7:
            factor = min(self.max_step, 1 + metrics.edge * 0.5)
            policy.capital *= factor
            return True

        return False
