import time

from clawbot.core.engine import Engine
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.infra.logger import log


def main():
    log("PHASE96", status="STARTED", mode="SOFT_RUN_SAFE")

    engine = Engine(policy=Phase96SoftPolicy())

    while True:
        engine.run_once()
        time.sleep(60)


if __name__ == "__main__":
    main()
