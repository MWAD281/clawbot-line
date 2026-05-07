# clawbot/governance/constitution.py

class Constitution:
    """
    กฎสูงสุดของกองทุน AI
    ห้าม policy / engine / agent ใด ๆ ละเมิด
    """

    MAX_DRAWDOWN = 0.30
    MAX_RISK_PER_TRADE = 0.02
    ALLOW_REAL_MONEY = False

    @classmethod
    def check(cls, decision: dict) -> bool:
        """
        ตรวจว่าการตัดสินใจละเมิดรัฐธรรมนูญหรือไม่
        """
        if decision.get("risk", 0) > cls.MAX_RISK_PER_TRADE:
            return False
        return True
