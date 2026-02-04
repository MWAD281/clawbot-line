from dataclasses import dataclass

@dataclass
class Decision:
    action: str        # "trade" | "hold"
    confidence: float  # 0.0 - 1.0
    reason: str
