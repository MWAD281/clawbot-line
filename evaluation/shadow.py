class ShadowPortfolio:
    """
    Compare policy vs benchmark
    """

    def __init__(self):
        self.policy_equity = 1.0
        self.benchmark_equity = 1.0

    def update(self, decision, benchmark_return):
        if decision.is_trade:
            self.policy_equity *= (1 + (decision.pnl or 0))

        self.benchmark_equity *= (1 + benchmark_return)

    def alpha(self):
        return self.policy_equity - self.benchmark_equity
