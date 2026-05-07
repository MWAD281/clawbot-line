from .rules import RegulationRule

REGULATIONS = {
    "US": {
        "crypto_futures": RegulationRule("US Futures", allowed=False),
        "crypto_spot": RegulationRule("US Spot", allowed=True),
    },
    "SG": {
        "crypto_futures": RegulationRule("SG Futures", allowed=True, max_leverage=10),
        "crypto_spot": RegulationRule("SG Spot", allowed=True),
    },
    "TH": {
        "crypto_futures": RegulationRule("TH Futures", allowed=False),
        "crypto_spot": RegulationRule("TH Spot", allowed=True),
    },
}

def check_permission(country, product):
    rule = REGULATIONS.get(country, {}).get(product)
    if not rule:
        return False, None
    return rule.allowed, rule.max_leverage
