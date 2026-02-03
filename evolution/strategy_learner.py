# evolution/strategy_learner.py

from memory.strategy_memory import record_strategy


def learn_from_judgment(judgment: dict):
    stance = judgment.get("stance")
    regime = judgment.get("regime")
    confidence = judgment.get("confidence", 0.5)

    if not stance or not regime:
        return

    # ใช้ confidence เป็น proxy outcome
    score = (confidence - 0.5) * 2
    record_strategy(stance, regime, score)
