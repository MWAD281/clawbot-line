from clawbot.core.engine import Engine
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.adapters.legacy_phase96 import LegacyPhase96Adapter
from clawbot.execution.executor import Executor
from clawbot.evaluation.judge import Judge
from clawbot.evaluation.metrics import Metrics

policy = Phase96SoftPolicy()
adapter = LegacyPhase96Adapter()
executor = Executor(mode="SOFT_RUN_SAFE")
judge = Judge()
metrics = Metrics()

engine = Engine(
    policy=policy,
    adapter=adapter,
    executor=executor,
    judge=judge,
    metrics=metrics
)

engine.run_forever()
