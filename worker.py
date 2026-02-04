import time
from clawbot.core.engine import Engine

# ใช้ market เดิมของคุณ
from world.market_probe import get_market_snapshot

engine = Engine(mode="SOFT_RUN_SAFE")

print("PHASE96 | clawbot-phase-96-worker STARTED | mode=SOFT_RUN_SAFE")

while True:
    market = get_market_snapshot()
    engine.step(market)
    time.sleep(5)
