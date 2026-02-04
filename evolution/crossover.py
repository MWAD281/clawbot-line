import copy
import random
from clawbot.policies.phase96_soft import Phase96SoftPolicy


def crossover(parent_a, parent_b):
    child = Phase96SoftPolicy()

    # inherit traits
    child.confidence_threshold = random.choice(
        [parent_a.confidence_threshold, parent_b.confidence_threshold]
    )

    child.risk_level = random.choice(
        [parent_a.risk_level, parent_b.risk_level]
    )

    child.timing_bias = random.choice(
        [parent_a.timing_bias, parent_b.timing_bias]
    )

    # small random drift
    child.confidence_threshold += random.uniform(-0.03, 0.03)
    child.risk_level += random.uniform(-0.05, 0.05)

    child.confidence_threshold = clamp(child.confidence_threshold, 0.4, 0.95)
    child.risk_level = clamp(child.risk_level, 0.1, 1.0)

    child.name = f"cross::{parent_a.name}+{parent_b.name}"

    return child


def clamp(v, lo, hi):
    return max(lo, min(hi, v))
