# clawbot/governance/council.py

class Council:
    """
    Council = กลุ่ม policy / judge / risk module
    """

    def __init__(self):
        self.members = []

    def register(self, member):
        self.members.append(member)

    def vote(self, decision: dict) -> dict:
        """
        รวมความเห็น (stub)
        """
        return {
            "approved": True,
            "confidence": 1.0,
            "notes": "Council placeholder"
        }
