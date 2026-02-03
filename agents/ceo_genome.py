# agents/ceo_genome.py

import random
import copy

def spawn_ceo(parent_name: str, parent_profile: dict) -> dict:
    """
    Clone + Mutate CEO
    """
    new_profile = copy.deepcopy(parent_profile)

    # mutation
    mutation = random.choice([
        "risk_downside",
        "growth_upside",
        "systemic_risk",
        "liquidity_focus",
        "geopolitical_focus"
    ])

    new_profile["bias"] = mutation
    new_profile["weight"] = round(random.uniform(0.6, 1.2), 2)
    new_profile["alive"] = True
    new_profile["memory"] = []

    return new_profile


def should_die(profile: dict) -> bool:
    return profile.get("weight", 1.0) <= 0.15
