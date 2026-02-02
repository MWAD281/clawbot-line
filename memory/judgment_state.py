import json
import os

STATE_FILE = "memory/world_judgment.json"

DEFAULT_STATE = {
    "global_risk": "UNKNOWN",
    "worldview": "UNSET",
    "stance": "NEUTRAL",
    "inertia": 1.0
}


def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_judgment():
    return load_state()


def overwrite_judgment(new_state: dict):
    save_state(new_state)
