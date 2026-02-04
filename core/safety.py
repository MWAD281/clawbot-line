def soft_guard(decision):
    if decision.confidence < 0.2:
        decision.action = "hold"
        decision.reason += " | soft_guard_triggered"
    return decision
