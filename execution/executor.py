from .impact import estimate_impact

class ImpactAwareExecutor:
    def execute(self, decision, market):
        impact = estimate_impact(
            decision["size"], market["volume"]
        )

        if impact > 0.02:
            return {
                "action": "SPLIT_ORDER",
                "chunks": int(impact / 0.01) + 1
            }

        if impact > 0.05:
            return {"action": "SKIP_TRADE"}

        return {"action": "EXECUTE"}
