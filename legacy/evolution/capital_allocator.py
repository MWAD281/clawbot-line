class CapitalAllocator:
    """
    Allocate capital across competing policies
    """

    def __init__(self, total_capital=1.0):
        self.total_capital = total_capital
        self.allocations = {}

    def allocate(self, policies):
        scores = [
            max(p.metrics.current_equity, 0.01)
            for p in policies
        ]
        total_score = sum(scores)

        self.allocations = {}

        for policy, score in zip(policies, scores):
            weight = score / total_score
            self.allocations[policy.name] = weight

        return self.allocations

    def capital_for(self, policy_name):
        return self.total_capital * self.allocations.get(policy_name, 0)
