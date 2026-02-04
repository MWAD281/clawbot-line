from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorldState:
    timestamp: datetime
    market: str = "SIMULATED"
    volatility: str = "UNKNOWN"
    data: dict = None
