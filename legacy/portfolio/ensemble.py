class EnsemblePortfolio:
    """
    Run multiple champion policies together
    """

    def __init__(self, allocator):
        self.policies = []
        self.allocator = allocator

    def add_policy(self, policy):
        self.policies.append(policy)

    def decide(self, world):
        allocations = self.allocator.allocate(self.policies)
        decisions = []

        for p in self.policies:
            capital = self.allocator.capital_for(p.name)
            d = p.decide(world)

            if d.is_trade:
                d.size *= capital

            decisions.append(d)

        return decisions
