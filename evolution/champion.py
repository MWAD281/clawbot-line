import copy


class ChampionFreezer:
    """
    Freeze best genome when dominance is clear
    """

    def __init__(self, alpha_threshold=0.15):
        self.champion = None
        self.alpha_threshold = alpha_threshold

    def consider(self, policy, shadow):
        if shadow.alpha() >= self.alpha_threshold:
            self.champion = copy.deepcopy(policy.genome)
            return True
        return False
