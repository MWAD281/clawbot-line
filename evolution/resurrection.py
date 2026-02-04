import copy
import random


class CapitalResurrector:
    """
    Revive dead policies with mutation
    """

    def resurrect(self, dead_policy, base_genome):
        new_genome = copy.deepcopy(base_genome)

        for regime in new_genome:
            for k in new_genome[regime]:
                new_genome[regime][k] *= random.uniform(0.9, 1.1)

        dead_policy.genome = new_genome
        dead_policy.metrics.reset()

        return dead_policy
