from collections import deque


class RegimeMemory:
    """
    Track regime transitions
    """

    def __init__(self, max_len=50):
        self.history = deque(maxlen=max_len)

    def record(self, regime_name):
        self.history.append(regime_name)

    def transition_score(self, current):
        if not self.history:
            return 0.0

        changes = sum(
            1 for r in self.history if r != current
        )
        return changes / len(self.history)
