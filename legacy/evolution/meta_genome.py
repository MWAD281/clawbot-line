import random


class MetaGenome:
    """
    Genome that controls how policies evolve
    """

    def __init__(self):
        self.mutation_rate = random.uniform(0.05, 0.25)
        self.crossover_rate = random.uniform(0.1, 0.5)
        self.extinction_threshold = random.uniform(0.6, 0.8)

    def mutate(self):
        self.mutation_rate *= random.uniform(0.9, 1.1)
        self.crossover_rate *= random.uniform(0.9, 1.1)
        self.extinction_threshold *= random.uniform(0.95, 1.05)

        self.mutation_rate = min(max(self.mutation_rate, 0.01), 0.5)
        self.crossover_rate = min(max(self.crossover_rate, 0.05), 0.8)
        self.extinction_threshold = min(max(self.extinction_threshold, 0.5), 0.9)
