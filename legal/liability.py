# clawbot/legal/liability.py

class Liability:
    """
    ใครรับผิดอะไร
    """

    def __init__(self):
        self.map = {
            "AI": "decision",
            "Operator": "execution",
            "Owner": "capital"
        }
