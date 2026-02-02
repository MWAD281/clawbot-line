# memory/agent_lifecycle.py

_agent_stats = {}


def record_performance(agent_id, confidence):
    _agent_stats.setdefault(agent_id, {
        "score": 0,
        "age": 0
    })

    _agent_stats[agent_id]["score"] += confidence
    _agent_stats[agent_id]["age"] += 1


def should_die(agent_id):
    data = _agent_stats.get(agent_id)
    if not data:
        return False

    return data["age"] > 30 and data["score"] < -3
