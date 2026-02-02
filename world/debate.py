# world/debate.py

from world.ceos.optimist import OptimistCEO
from world.ceos.pessimist import PessimistCEO
from world.ceos.realist import RealistCEO
from world.ceos.strategist import StrategistCEO
from world.ceos.survivor import SurvivorCEO

CEOS = [
    OptimistCEO(),
    PessimistCEO(),
    RealistCEO(),
    StrategistCEO(),
    SurvivorCEO()
]


def run_ceo_debate(text: str, world_state: dict):
    return [ceo.vote(text, world_state) for ceo in CEOS]
