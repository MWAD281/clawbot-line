import time

class Clock:
    def now(self) -> float:
        return time.time()

    def sleep(self, seconds: float):
        time.sleep(seconds)
