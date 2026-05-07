# clawbot/legal/entity.py

class LegalEntity:
    """
    โครงสร้างความสัมพันธ์ทางกฎหมาย
    """

    def __init__(self, owner: str, operator: str):
        self.owner = owner
        self.operator = operator
        self.ai = "ClawBot"

    def summary(self):
        return {
            "owner": self.owner,
            "operator": self.operator,
            "ai": self.ai
        }
