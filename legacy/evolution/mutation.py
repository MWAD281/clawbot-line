import random
import copy
from clawbot.policies.phase96_soft import Phase96SoftPolicy


def mutate_policy(parent=None):
    if parent:
        base = copy.deepcopy(parent)
        name_seed = parent.name
    else:
        base = Phase96SoftPolicy()
        name_seed = "genesis"

    # ===== mutation dimensions =====
    base.confidence_threshold = clamp(
        base.confidence_threshold + random.uniform(-0.1, 0.1),
        0.4,
        0.95,
    )

    base.risk_level = clamp(
        base.risk_level + random.uniform(-0.2, 0.2),
        0.1,
        1.0,
    )

    base.timing_bias = random.choice(
        [-1, 0, 1]
    ) if random.random() < 0.3 else base.timing_bias

    base.name = f"mutant::{name_seed}"

    return base


def clamp(v, lo, hi):
    return max(lo, min(hi, v))
