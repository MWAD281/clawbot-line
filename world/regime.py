# world/regime.py

from memory.agent_weights import adjust_weight, revive_agent
from memory.judgment_state import get_judgment, overwrite_judgment

# 🏛️ Regime definition
REGIME_MAP = {
    "RISK_OFF": {
        "worldview": "FRAGILE_COMPLEX_SYSTEM",
        "stance": "DEFENSIVE",
        "boost": ["CEO_ALPHA"],
        "nerf": ["CEO_BETA"]
    },
    "RISK_ON": {
        "worldview": "OPPORTUNITY_DRIVEN_SYSTEM",
        "stance": "OPPORTUNISTIC",
        "boost": ["CEO_BETA"],
        "nerf": ["CEO_ALPHA"]
    }
}


def apply_regime_shift(dominant_faction: str):
    """
    เปลี่ยนโลกแบบ discontinuous ตาม faction ที่ชนะ
    """

    if dominant_faction not in REGIME_MAP:
        return

    regime = REGIME_MAP[dominant_faction]
    state = get_judgment()

    # 🌍 Update world core belief
    overwrite_judgment({
        **state,
        "worldview": regime["worldview"],
        "stance": regime["stance"],
        "regime": dominant_faction
    })

    # 🔊 Boost winners
    for agent in regime["boost"]:
        revive_agent(agent, weight=1.2)

    # 🔇 Nerf losers
    for agent in regime["nerf"]:
        adjust_weight(agent, -0.4)
