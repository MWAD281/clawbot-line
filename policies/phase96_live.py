from clawbot.policies.base import Policy


class Phase96LivePolicy(Policy):
    def decide(self, world):
        raise NotImplementedError("Live mode not enabled yet")
