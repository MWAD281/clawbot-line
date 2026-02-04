class Metrics:
    def __init__(self):
        self.trades = []
        self.current_equity = 1.0
        self.max_equity = 1.0

    def record(self, decision):
        self.trades.append(decision)

        if decision.is_trade:
            pnl = decision.pnl or 0
            self.current_equity *= (1 + pnl)

            if self.current_equity > self.max_equity:
                self.max_equity = self.current_equity
