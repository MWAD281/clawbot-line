# memory/strategy_memory.py

from collections import defaultdict

# key = (stance, regime)
# value = { win, loss, score }
STRATEGY_MEMORY = defaultdict(lambda: {
    "win": 0,
    "loss": 0,
    "score": 0.0
})


def record_strategy(stance: str, regime: str, score: float):
    key = (stance, regime)

    if score > 0:
        STRATEGY_MEMORY[key]["win"] += 1
    else:
        STRATEGY_MEMORY[key]["loss"] += 1

    STRATEGY_MEMORY[key]["score"] += score


def get_strategy_bias(stance: str, regime: str) -> float:
    key = (stance, regime)
    data = STRATEGY_MEMORY.get(key)

    if not data:
        return 0.0

    total = data["win"] + data["loss"]
    if total == 0:
        return 0.0

    winrate = data["win"] / total
    return (winrate - 0.5) * 2   # -1 → +1


def dump_strategy_memory():
    return dict(STRATEGY_MEMORY)
