class Population:
    def __init__(self, policies, min_size=3, max_size=8):
        self.policies = policies
        self.min_size = min_size
        self.max_size = max_size

    def rank(self):
        return sorted(
            self.policies,
            key=lambda p: p.metrics.snapshot()["avg_score"],
            reverse=True,
        )

    def kill_losers(self, kill_ratio=0.3):
        ranked = self.rank()
        kill_count = max(1, int(len(ranked) * kill_ratio))

        losers = ranked[-kill_count:]
        survivors = ranked[:-kill_count]

        for p in losers:
            print(f"☠️ Darwin kill policy {p.name}")

        self.policies = survivors

    def add(self, policy):
        self.policies.append(policy)

    def ensure_minimum(self, factory):
        while len(self.policies) < self.min_size:
            newborn = factory()
            print(f"🧬 Spawn new policy {newborn.name}")
            self.policies.append(newborn)
