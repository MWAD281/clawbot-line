# clawbot/governance/veto.py

class Veto:
    """
    Kill-switch ระดับกองทุน
    """

    def __init__(self):
        self.triggered = False
        self.reason = None

    def trigger(self, reason: str):
        self.triggered = True
        self.reason = reason
