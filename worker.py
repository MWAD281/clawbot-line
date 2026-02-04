# worker.py

import time
from core.engine import Engine
from policies.phase96_soft import Phase96SoftPolicy

def run():
    policy = Phase96SoftPolicy()
    engine = Engine(policy=policy, mode="SOFT_RUN_SAFE")

    while True:
        engine.step(world=None)
        time.sleep(5)

if __name__ == "__main__":
    run()
