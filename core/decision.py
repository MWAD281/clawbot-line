from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Decision:
    action: str
    confidence: float
    reason: str
    meta: Dict[str, Any]
