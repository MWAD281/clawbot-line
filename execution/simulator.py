class TradeSimulator:
    def execute(self, decision, world):
        return {
            "status": "SIMULATED",
            "action": decision.action,
            "confidence": decision.confidence,
            "cycle": world["cycle"],
            "timestamp": world["timestamp"],
            "note": "no real trade executed"
        }
