import copy


class MarketTransfer:
    """
    Transfer knowledge between markets
    """

    def extract_traits(self, policy):
        return {
            "risk": policy.genome["risk"],
            "timing": policy.genome["timing"],
            "volatility_response": policy.genome.get("volatility_response", 1.0),
        }

    def inject_traits(self, policy, traits, strength=0.5):
        for k, v in traits.items():
            if k in policy.genome:
                policy.genome[k] = (
                    policy.genome[k] * (1 - strength) + v * strength
                )

        return policy
