import logging
from datetime import date

from app.config import get_settings
from app.services.openai_service import create_completion
from app.services.sheets_service import get_crm_sheet
from app.services.line_service import push_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """คุณคือ Sales Director Agent ของ CERAFIELD Thailand
หน้าที่: วิเคราะห์ lead และ draft ข้อความ follow-up ที่เป็นมืออาชีพ อบอุ่น กระชับ
สไตล์: ภาษาไทย professional มีชื่อ lead และบริษัท ถามความคืบหน้าโครงการ
ห้ามบอกราคา ห้ามสัญญาอะไรที่เกินอำนาจ"""


async def run_sales_agent() -> None:
    settings = get_settings()
    if not settings.tony_line_user_id:
        logger.warning("TONY_LINE_USER_ID not set — skipping Sales Agent")
        return

    try:
        ws = get_crm_sheet("🎯 Leads")
        if ws is None:
            logger.warning("Sales Agent: cannot access CRM")
            return

        rows = ws.get_all_records()
        today = date.today()
        overdue = []

        for row in rows:
            stage = str(row.get("Stage", "")).lower()
            if "closed" in stage or "lost" in stage or "won" in stage:
                continue
            next_date_str = str(row.get("Next Action Date", "")).strip()
            if not next_date_str:
                continue
            try:
                parts = next_date_str.split("/")
                if len(parts) == 3:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    next_date = date(y, m, d)
                    if next_date <= today:
                        overdue.append(row)
            except Exception:
                continue

        if not overdue:
            await push_text(
                settings.tony_line_user_id,
                "Sales Agent: ไม่มี lead ที่ต้อง follow-up วันนี้ค่ะ"
            )
            return

        lines = [f"Sales Agent — Follow-Up วันนี้ ({today.strftime('%d/%m/%Y')})\n"]
        for lead in overdue[:5]:
            name = lead.get("Name", "-")
            company = lead.get("Company", "-")
            lead_type = lead.get("Type", "-")
            stage = lead.get("Stage", "-")
            notes = lead.get("Notes", "")

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Lead: {name} | บริษัท: {company} | ประเภท: {lead_type} | "
                    f"Stage: {stage} | Notes: {notes}\n"
                    "Draft ข้อความ LINE สั้นๆ สำหรับ follow-up (ไม่เกิน 3 บรรทัด)"
                )},
            ]
            resp = await create_completion(messages)
            draft = resp.choices[0].message.content or ""
            lines.append(f"[{name} — {company}]\n{draft}\n")

        await push_text(settings.tony_line_user_id, "\n".join(lines))
        logger.info("Sales Agent sent follow-up for %d leads", len(overdue))

    except Exception as e:
        logger.error("Sales Agent error: %s", type(e).__name__)
