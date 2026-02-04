class Population:
    def __init__(self, policies, min_size=3, max_size=8, mutator=None):
        self.policies = policies
        self.min_size = min_size
        self.max_size = max_size
        self.mutator = mutator

    def rank(self):
        return sorted(
            self.policies,
            key=lambda p: p.metrics.snapshot()["avg_score"],
            reverse=True,
        )

    def evolve(self, kill_ratio=0.3):
        ranked = self.rank()
        kill_count = max(1, int(len(ranked) * kill_ratio))

        losers = ranked[-kill_count:]
        survivors = ranked[:-kill_count]

        for p in losers:
            print(f"☠️ Darwin kill {p.name}")

        self.policies = survivors

        # === Phase F+ : Auto mutation ===
        if self.mutator:
            while len(self.policies) < self.max_size:
                newborn = self.mutator()
                print(f"🧬 Mutation spawn {newborn.name}")
                self.policies.append(newborn)

    def snapshot(self):
        return [
            {
                "policy": p.name,
                "metrics": p.metrics.snapshot(),
            }
            for p in self.policies
        ]
