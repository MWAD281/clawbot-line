# clawbot/legacy/phase96_adapter.py

from core.decision import Decision
from market.market_probe import get_market_snapshot
from evolution.strategy_pool import load_strategies
import random

class LegacyPhase96Adapter:
    phase = "PHASE96"

    def __init__(self):
        self.strategies = load_strategies()

    def decide(self, world=None):
        market = get_market_snapshot()

        # legacy logic (ย่อจากของเดิม)
        chosen = random.choice(self.strategies)

        return Decision(
            action="NO_TRADE",
            confidence=chosen.get("edge", 0.0),
            reason="legacy_phase96_adapter",
            meta={
                "strategy_id": chosen.get("id"),
                "volatility": market.get("volatility")
            }
        )
