from clawbot.core.engine import Engine
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.adapters.legacy_phase96 import LegacyPhase96Adapter

policy = Phase96SoftPolicy()
adapter = LegacyPhase96Adapter()

engine = Engine(
    policy=policy,
    adapter=adapter
)

engine.run_forever(interval_sec=60)
