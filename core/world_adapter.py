# clawbot/core/world_adapter.py

from world.market_probe import get_market_snapshot

class WorldAdapter:
    def observe(self):
        return get_market_snapshot()
