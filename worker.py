from clawbot.core.engine import Engine
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.infra.config import PHASE96_INTERVAL_SEC

def start_phase96_soft():
    engine = Engine(
        policy=Phase96SoftPolicy(),
        interval_sec=PHASE96_INTERVAL_SEC
    )
    engine.run_forever()

if __name__ == "__main__":
    start_phase96_soft()
