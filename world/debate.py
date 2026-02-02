# world/debate.py

from agents.ceo_alpha import ceo_alpha
from agents.ceo_beta import ceo_beta
from agents.ceo_gamma import ceo_gamma

def run_ceo_debate(user_input: str, world_state: dict):
    return [
        ceo_alpha(user_input, world_state),
        ceo_beta(user_input, world_state),
        ceo_gamma(user_input, world_state),
    ]
