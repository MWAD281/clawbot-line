from clawbot.core.decision import Decision
import random

def decide(market_snapshot: dict) -> Decision:
    confidence = random.uniform(0.1, 0.9)

    action = "trade" if confidence > 0.6 else "hold"
    reason = "phase96_soft_policy"

    return Decision(
        action=action,
        confidence=confidence,
        reason=reason
    )
