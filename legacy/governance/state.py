# clawbot/governance/state.py

from enum import Enum


class FundState(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FROZEN = "FROZEN"
    EMERGENCY_STOP = "EMERGENCY_STOP"
