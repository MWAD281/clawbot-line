import random


class Judge:
    """
    Phase E:
    - ประเมิน trade แบบง่ายก่อน
    - ยังไม่ใช้ market จริง
    """

    def evaluate(self, decision, execution_result):
        if decision.action != "TRADE":
            return 0.0, "no_trade"

        # จำลอง outcome (Phase E)
        outcome = random.choice(["win", "lose"])

        if outcome == "win":
            score = decision.confidence
            reason = "simulated_win"
        else:
            score = -decision.confidence
            reason = "simulated_loss"

        return score, reason
