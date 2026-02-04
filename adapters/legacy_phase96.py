from clawbot.core.decision import Decision

# 🔧 แก้ import ตรงนี้ให้ตรงกับของเดิม
from phases.phase96 import run_phase96_once


class LegacyPhase96Adapter:
    def execute(self, world):
        result = run_phase96_once()

        # แปลงผลลัพธ์เดิม → Decision ใหม่
        return Decision(
            action=result.get("action", "HOLD"),
            confidence=result.get("confidence", 0.0),
            reason="legacy_phase96",
            meta=result
        )
