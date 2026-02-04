class CoEvolution:
    def adapt_policy(self, policy, feedbacks):
        for f in feedbacks:
            if f["ai_decision"] != f["human_action"]:
                policy.genome["confidence_decay"] = (
                    policy.genome.get("confidence_decay", 1.0) * 0.95
                )
        return policy
