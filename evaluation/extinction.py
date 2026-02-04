class ExtinctionRule:
    """
    Kill policy if drawdown exceeds tolerance
    """

    def __init__(self, max_drawdown=0.25):
        self.max_drawdown = max_drawdown

    def should_kill(self, metrics):
        """
        metrics must expose:
        - max_equity
        - current_equity
        """
        if metrics.max_equity == 0:
            return False

        drawdown = (
            metrics.max_equity - metrics.current_equity
        ) / metrics.max_equity

        return drawdown >= self.max_drawdown
