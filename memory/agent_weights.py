# memory/agent_weights.py

AGENT_WEIGHTS = {}

DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.1
MAX_WEIGHT = 3.0

def get_weight(agent_id: str) -> float:
    return AGENT_WEIGHTS.get(agent_id, DEFAULT_WEIGHT)

def adjust_weight(agent_id: str, delta: float):
    current = AGENT_WEIGHTS.get(agent_id, DEFAULT_WEIGHT)
    new_weight = max(MIN_WEIGHT, min(MAX_WEIGHT, current + delta))
    AGENT_WEIGHTS[agent_id] = new_weight
