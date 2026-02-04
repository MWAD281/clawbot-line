from clawbot.evaluation.metrics import (
    survival_score,
    regret_score,
    stability_score
)

def judge(decision) -> dict:
    return {
        "survival": survival_score(decision),
        "regret": regret_score(decision),
        "stability": stability_score(decision),
    }
