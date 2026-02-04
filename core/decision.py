from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Decision:
    action: str
    confidence: float
    reason: str
    risk: float = 0.0
    meta: Dict[str, Any] = None

    def as_dict(self):
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reason": self.reason,
            "risk": self.risk,
            "meta": self.meta or {},
        }
