import logging
from collections import Counter
from datetime import date

from app.config import get_settings
from app.services.openai_service import create_completion
from app.services.sheets_service import get_crm_sheet
from app.services.line_service import push_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """คุณคือ CEO Agent ของ CERAFIELD Thailand
หน้าที่: สรุป weekly executive memo จากข้อมูล pipeline จริง
สไตล์: Direct, strategic, กระชับ ไม่มีคำพูดที่ไม่จำเป็น
ต้องมี: สรุปสถานะ, จุดเสี่ยง, priority action 3 ข้อสำหรับสัปดาห์นี้"""


async def run_ceo_agent() -> None:
    settings = get_settings()
    if not settings.tony_line_user_id:
        logger.warning("TONY_LINE_USER_ID not set — skipping CEO Agent")
        return

    try:
        ws = get_crm_sheet("🎯 Leads")
        if ws is None:
            logger.warning("CEO Agent: cannot access CRM")
            return

        rows = ws.get_all_records()
        total = len(rows)
        stage_counts = Counter(str(r.get("Stage", "Unknown")) for r in rows)
        priority_counts = Counter(str(r.get("Priority", "")) for r in rows)
        types = Counter(str(r.get("Type", "")) for r in rows)

        stage_summary = " | ".join(f"{k}: {v}" for k, v in stage_counts.most_common())
        type_summary = " | ".join(f"{k}: {v}" for k, v in types.most_common())
        today = date.today()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"วันที่: {today.strftime('%d/%m/%Y')} (วันจันทร์ — Weekly Review)\n\n"
                f"Pipeline Data:\n"
                f"- Total leads: {total}\n"
                f"- By stage: {stage_summary}\n"
                f"- By type: {type_summary}\n"
                f"- High priority: {priority_counts.get('High', 0)} leads\n\n"
                "สรุป CEO Weekly Memo ไม่เกิน 15 บรรทัด"
            )},
        ]
        resp = await create_completion(messages)
        memo = resp.choices[0].message.content or ""

        message = (
            f"CEO Agent — Weekly Memo {today.strftime('%d/%m/%Y')}\n\n"
            f"{memo}"
        )
        await push_text(settings.tony_line_user_id, message)
        logger.info("CEO Agent sent weekly memo")

    except Exception as e:
        logger.error("CEO Agent error: %s", type(e).__name__)
