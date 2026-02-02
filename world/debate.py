# world/debate.py

from agents.ceo_alpha import ceo_alpha

def run_ceo_debate(user_input: str, world_state: dict):
    """
    เรียก CEO ทุกคนมาโหวต
    (ตอนนี้ยังมีแค่ Alpha)
    """

    votes = []

    votes.append(
        ceo_alpha(user_input, world_state)
    )

    return votes
