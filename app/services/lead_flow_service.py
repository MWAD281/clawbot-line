"""
Lead capture flow for 50-99 pcs inquiries.
Triggered by [LEAD_FORM] from the AI engine.
Collects: ชื่อ / เบอร์โทร / Email / LINE ID → saves to Sheets "📋 Leads".
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.services.sheets_service import append_to_sheet

logger = logging.getLogger(__name__)

CANCEL_WORDS = {"ยกเลิก", "cancel", "ออก", "หยุด", "exit"}

_COLLECT_PROMPT = (
    "กรอกข้อมูลด้านล่างนี้ได้เลยค่ะ (ในข้อความเดียว):\n\n"
    "ชื่อ-นามสกุล:\n"
    "เบอร์โทร:\n"
    "Email:\n"
    "LINE ID:"
)


@dataclass
class LeadReply:
    text: str
    quick_reply: Optional[List[str]] = field(default=None)


async def start_lead_flow(user_id: str, store) -> LeadReply:
    await store.set_lead_flow(user_id, {"step": "collect"})
    return LeadReply(text=_COLLECT_PROMPT)


async def handle_lead_flow(user_id: str, text: str, store) -> Optional[LeadReply]:
    """Returns LeadReply if user is in an active lead flow, None otherwise."""
    state = await store.get_lead_flow(user_id)
    if state is None:
        return None

    t = text.strip()

    if t.lower() in CANCEL_WORDS:
        await store.clear_lead_flow(user_id)
        return LeadReply(text="ยกเลิกแล้วค่ะ ถ้าสนใจสอบถามได้ตลอดเวลานะคะ")

    if state.get("step") == "collect":
        await store.clear_lead_flow(user_id)
        _save_lead(user_id, t)
        _notify_admin(user_id, t)
        return LeadReply(
            text="ขอบคุณค่ะ ทีม AE จะติดต่อกลับภายใน 24 ชั่วโมงค่ะ\nถ้ามีคำถามเพิ่มเติมสอบถามได้เลยนะคะ"
        )

    await store.clear_lead_flow(user_id)
    return None


def _save_lead(user_id: str, info_text: str) -> None:
    try:
        now = datetime.now()
        append_to_sheet("📋 Leads", [
            now.strftime("%d/%m/%Y"),
            now.strftime("%H:%M"),
            user_id,
            info_text[:500],
            "New",
            "",
        ])
    except Exception as e:
        logger.warning("Lead save failed: %s", e)


def _notify_admin(user_id: str, info_text: str) -> None:
    try:
        from app.config import get_settings
        from app.services.line_service import push_text
        tony_id = get_settings().tony_line_user_id
        if not tony_id:
            return
        msg = (
            f"🙋 Lead ใหม่ (50-99 ชิ้น)\n"
            f"LINE: {user_id[:12]}...\n\n"
            f"{info_text[:300]}"
        )
        asyncio.create_task(push_text(tony_id, msg))
    except Exception as e:
        logger.warning("Lead admin notify failed: %s", e)
