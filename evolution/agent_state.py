# evolution/agent_state.py

AGENT_STATE = {
    "fitness": 0,
    "lives": 3,
    "status": "ALIVE",  # ALIVE | DEAD
    "generation": 1
}


def update_fitness(delta: int):
    AGENT_STATE["fitness"] += delta

    if delta < 0:
        AGENT_STATE["lives"] -= 1

    if AGENT_STATE["lives"] <= 0:
        AGENT_STATE["status"] = "DEAD"

    return AGENT_STATE


def rebirth():
    AGENT_STATE["fitness"] = 0
    AGENT_STATE["lives"] = 3
    AGENT_STATE["status"] = "ALIVE"
    AGENT_STATE["generation"] += 1

    return AGENT_STATE
