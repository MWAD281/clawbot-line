# clawbot/policies/phase96_soft.py

from legacy.phase96_adapter import LegacyPhase96Adapter

class Phase96SoftPolicy:
    phase = "PHASE96_SOFT"

    def __init__(self):
        self.legacy = LegacyPhase96Adapter()

    def decide(self, world=None):
        return self.legacy.decide(world)
