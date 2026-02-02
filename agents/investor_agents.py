# agents/investor_agents.py

from memory.agent_weights import get_weight

def cautious_investor(world_input, world_state):
    return {
        "agent_id": "investor_cautious",
        "global_risk": "HIGH",
        "weight": get_weight("investor_cautious"),
        "reason": "Macro risk still elevated"
    }

def opportunistic_investor(world_input, world_state):
    return {
        "agent_id": "investor_opportunistic",
        "global_risk": "MEDIUM",
        "weight": get_weight("investor_opportunistic"),
        "reason": "Valuations attractive despite risk"
    }

def get_investor_views(world_input, world_state):
    return [
        cautious_investor(world_input, world_state),
        opportunistic_investor(world_input, world_state),
    ]
