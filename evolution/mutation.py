import random
from clawbot.policies.phase96_soft import Phase96SoftPolicy


def mutate_policy():
    """
    Phase F mutation:
    - เปลี่ยน threshold เล็กน้อย
    """
    base = Phase96SoftPolicy()

    jitter = random.uniform(-0.15, 0.15)
    base.confidence_bias = max(0.1, min(0.9, base.confidence_bias + jitter))
    base.name = f"phase96_mut_{round(base.confidence_bias, 2)}"

    return base
