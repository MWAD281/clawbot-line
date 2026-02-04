# clawbot/legal/jurisdiction.py

class Jurisdiction:
    """
    ขอบเขตกฎหมาย
    """

    def __init__(self, country: str):
        self.country = country

    def allow_trading(self) -> bool:
        return True  # stub
