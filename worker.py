from clawbot.core.engine import Engine
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.adapters.legacy_phase96 import LegacyPhase96Adapter
from clawbot.execution.executor import Executor

policy = Phase96SoftPolicy()
adapter = LegacyPhase96Adapter()
executor = Executor(mode="SOFT_RUN_SAFE")

engine = Engine(
    policy=policy,
    adapter=adapter,
    executor=executor
)

engine.run_forever()
