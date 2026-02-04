class Metrics:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.fail = 0
        self.score_sum = 0.0

    def record(self, score: float):
        self.total += 1
        self.score_sum += score

        if score > 0:
            self.success += 1
        else:
            self.fail += 1

    def snapshot(self):
        if self.total == 0:
            avg = 0
        else:
            avg = self.score_sum / self.total

        return {
            "total": self.total,
            "success": self.success,
            "fail": self.fail,
            "avg_score": round(avg, 4),
        }
