class RealMoneyGuard:
    """
    Final safety layer before real money
    """

    def __init__(self, max_drawdown=0.2, max_position=0.05):
        self.max_drawdown = max_drawdown
        self.max_position = max_position
        self.peak_equity = 1.0
        self.frozen = False

    def check(self, policy):
        equity = policy.metrics.current_equity
        self.peak_equity = max(self.peak_equity, equity)

        drawdown = 1 - equity / self.peak_equity

        if drawdown >= self.max_drawdown:
            self.frozen = True
            return False

        return True

    def throttle(self, decision):
        if decision.size > self.max_position:
            decision.size = self.max_position
        return decision
