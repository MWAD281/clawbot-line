import random
from clawbot.evolution.mutation import mutate_policy
from clawbot.evolution.crossover import crossover


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

    def evolve(self, kill_ratio=0.3):
        ranked = self.rank()
        kill_count = max(1, int(len(ranked) * kill_ratio))

        survivors = ranked[:-kill_count]
        elites = survivors[:2] if len(survivors) >= 2 else survivors

        self.policies = survivors

        # ===== Phase F++ / F+++ spawn =====
        while len(self.policies) < self.max_size:
            if len(elites) >= 2 and random.random() < 0.6:
                p1, p2 = random.sample(elites, 2)
                child = crossover(p1, p2)
            else:
                parent = random.choice(elites) if elites else None
                child = mutate_policy(parent)

            print(f"🧬 Spawn {child.name}")
            self.policies.append(child)

    def snapshot(self):
        return [
            {
                "policy": p.name,
                "metrics": p.metrics.snapshot(),
                "traits": {
                    "confidence_threshold": p.confidence_threshold,
                    "risk_level": p.risk_level,
                    "timing_bias": p.timing_bias,
                },
            }
            for p in self.policies
        ]
