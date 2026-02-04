class MetaJudge:
    """
    Decide which judge to trust based on regime & performance
    """

    def __init__(self, judges):
        self.judges = judges  # dict[name -> judge]
        self.weights = {name: 1.0 for name in judges}

    def score(self, policy, world):
        total = 0.0
        weight_sum = 0.0

        for name, judge in self.judges.items():
            s = judge.score(policy, world)
            w = self.weights.get(name, 1.0)
            total += s * w
            weight_sum += w

        return total / max(weight_sum, 1e-6)

    def update_weights(self, judge_results):
        """
        judge_results: dict[name -> correctness_score]
        """
        for name, correctness in judge_results.items():
            self.weights[name] *= (0.9 + 0.2 * correctness)
