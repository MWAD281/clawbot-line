# memory/ceo_memory.py

_ceo_memory = {}


def remember(agent_id: str, event: dict):
    _ceo_memory.setdefault(agent_id, [])
    _ceo_memory[agent_id].append(event)

    # จำกัด memory ล่าสุด 50 เหตุการณ์
    _ceo_memory[agent_id] = _ceo_memory[agent_id][-50:]


def recall(agent_id: str):
    return _ceo_memory.get(agent_id, [])
