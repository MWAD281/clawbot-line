import logging
from datetime import date

from app.config import get_settings
from app.services.openai_service import create_completion
from app.services.sheets_service import append_to_sheet
from app.services.line_service import push_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """คุณคือ Marketing Agent ของ CERAFIELD Thailand
สินค้า: สุขภัณฑ์ premium — โถส้วม, ราวจับนิรภัย, เก้าอี้อาบน้ำ
แบรนด์: premium, trustworthy, technically credible
ลูกค้า: Developer, Hotel, Architect, Contractor

หน้าที่: draft content สำหรับ LINE OA และ Social Media
กฎ:
- ภาษาไทย กระชับ เหมาะ mobile
- ห้ามใช้ Markdown
- มี call-to-action ทุกโพสต์
- ไม่บอกราคาตายตัว"""

CONTENT_THEMES = [
    ("Technical Authority", "เขียน post แนะนำ Tornado Flushing Technology ของ CERAFIELD — ทำไมถึงดีกว่าระบบทั่วไป เหมาะสำหรับ LINE OA"),
    ("Product Spotlight", "เขียน post แนะนำ CF-13022 สำหรับโปรเจกต์ที่ต้องการความสะดวกสบายสูงสุด เน้นที่นั่งกว้าง เหมาะ senior living"),
    ("Market Intelligence", "เขียน post เกี่ยวกับ trend ห้องน้ำในโรงแรมระดับ 4-5 ดาวของไทย 2026 เพื่อสร้าง credibility กับลูกค้า Hotel"),
    ("Project Solution", "เขียน post เกี่ยวกับ CF-2493 — ท่อ 50mm ลดการอุดตัน เหมาะโปรเจกต์ขนาดใหญ่ สำหรับ Developer และ Contractor"),
    ("Safety Focus", "เขียน post แนะนำ FLUSSO + TRAFFIXPRO series สำหรับ senior living และ accessible design เน้นความปลอดภัย"),
]


async def run_marketing_agent() -> None:
    settings = get_settings()
    if not settings.tony_line_user_id:
        logger.warning("TONY_LINE_USER_ID not set — skipping Marketing Agent")
        return

    try:
        today = date.today()
        drafts_written = 0

        for theme_name, prompt in CONTENT_THEMES:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{prompt}\nวันที่: {today.strftime('%d/%m/%Y')}"},
            ]
            resp = await create_completion(messages)
            draft = resp.choices[0].message.content or ""

            row = [
                today.strftime("%d/%m/%Y"),
                theme_name,
                "LINE OA / Social",
                draft,
                "Draft",
                "",
            ]
            append_to_sheet("📝 Marketing Drafts", row)
            drafts_written += 1

        message = (
            f"Marketing Agent — {drafts_written} drafts พร้อมแล้ว {today.strftime('%d/%m/%Y')}\n\n"
            "ดูและ approve ได้ใน Google Sheets tab: Marketing Drafts\n"
            "เมื่อ approve แล้วให้ copy ไปโพสต์ใน LINE OA / Social Media ค่ะ"
        )
        await push_text(settings.tony_line_user_id, message)
        logger.info("Marketing Agent wrote %d drafts", drafts_written)

    except Exception as e:
        logger.error("Marketing Agent error: %s", type(e).__name__)
