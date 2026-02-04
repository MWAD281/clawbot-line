from abc import ABC, abstractmethod
from clawbot.core.decision import Decision

class Policy(ABC):

    @abstractmethod
    def decide(self, world_state: dict) -> Decision:
        pass
