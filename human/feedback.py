class HumanFeedback:
    def __init__(self):
        self.overrides = []

    def record(self, decision, human_action, reason):
        self.overrides.append({
            "ai_decision": decision,
            "human_action": human_action,
            "reason": reason,
        })
