from world.ceos.base import BaseCEO


class OptimistCEO(BaseCEO):
    id = "optimist"
    faction = "GROWTH"
    personality = {
        "risk_tolerance": 0.8,
        "fear_sensitivity": 0.2
    }

    def think(self, text, world_state):
        risk = "HIGH" if "สงคราม" in text else "MEDIUM"

        confidence = 0.7 if risk != "HIGH" else 0.4

        return {
            "global_risk": risk,
            "confidence": confidence
        }
