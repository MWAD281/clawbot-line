from agents.ceo_alpha import ceo_alpha
from agents.ceo_beta import ceo_beta
from agents.ceo_gamma import ceo_gamma   # ✅ เพิ่ม

def run_ceo_debate(user_input: str, world_state: dict):
    votes = []

    votes.append(ceo_alpha(user_input, world_state))
    votes.append(ceo_beta(user_input, world_state))
    votes.append(ceo_gamma(user_input, world_state))  # ✅ เพิ่ม

    return votes
