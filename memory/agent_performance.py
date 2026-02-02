# memory/agent_performance.py

import json
import os

PERF_FILE = "memory/agent_performance.json"

DEFAULT = {
    "correct": 0,
    "wrong": 0,
    "streak": 0
}

def load_perf():
    if not os.path.exists(PERF_FILE):
        return {}
    with open(PERF_FILE, "r") as f:
        return json.load(f)

def save_perf(data):
    with open(PERF_FILE, "w") as f:
        json.dump(data, f, indent=2)

def record_result(agent_id: str, correct: bool):
    data = load_perf()
    perf = data.get(agent_id, DEFAULT.copy())

    if correct:
        perf["correct"] += 1
        perf["streak"] = max(1, perf["streak"] + 1)
    else:
        perf["wrong"] += 1
        perf["streak"] = min(-1, perf["streak"] - 1)

    data[agent_id] = perf
    save_perf(data)

def get_perf(agent_id: str):
    return load_perf().get(agent_id, DEFAULT.copy())
