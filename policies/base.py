from abc import ABC, abstractmethod


class Policy(ABC):
    @abstractmethod
    def decide(self, world):
        pass
