from clawbot.core.engine import Engine
from clawbot.evolution.population import Population
from clawbot.evolution.mutation import mutate_policy
from clawbot.policies.phase96_soft import Phase96SoftPolicy
from clawbot.adapters.legacy_phase96 import LegacyPhase96Adapter
from clawbot.execution.executor import Executor
from clawbot.evaluation.judge import Judge

policies = [Phase96SoftPolicy() for _ in range(5)]

population = Population(policies)

engine = Engine(
    population=population,
    adapter=LegacyPhase96Adapter(),
    executor=Executor(mode="SOFT_RUN_SAFE"),
    judge=Judge(),
)

engine.run_forever()
