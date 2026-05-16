import logging
from datetime import date

from app.config import get_settings
from app.services.openai_service import create_completion
from app.services.line_service import push_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """คุณคือ Competitor Intelligence Agent ของ CERAFIELD Thailand
ข้อมูลคู่แข่งที่รู้จัก:
- TOTO: market leader premium-luxury, ราคา ฿8,000-50,000+, แข็งแกร่งด้าน architect loyalty
- COTTO (SCG): mass-mid market Thai brand, ราคา ฿3,000-15,000, Thai brand loyalty
- American Standard: international mid-premium, ราคา ฿5,000-25,000
- Kohler: premium lifestyle ราคา ฿15,000-100,000+ (ไม่ใช่ direct competitor)
- Roca: European architectural, ราคา ฿8,000-40,000, import lead times นาน

CERAFIELD edge: OEM 35 ปี 28 ประเทศ, Tornado flushing, ceramic warranty 10 ปี, ราคา project ดีกว่า 15-25%

หน้าที่: สรุป weekly intelligence brief กระชับ actionable ไม่เกิน 10 บรรทัด
ห้ามแต่งข้อมูลที่ไม่รู้ — ถ้าไม่มีข้อมูลใหม่ให้บอกว่าไม่มีการเคลื่อนไหวที่ผิดปกติ"""


async def run_intelligence_agent() -> None:
    settings = get_settings()
    if not settings.tony_line_user_id:
        logger.warning("TONY_LINE_USER_ID not set — skipping Intelligence Agent")
        return

    try:
        today = date.today()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"วันที่: {today.strftime('%d/%m/%Y')}\n"
                "สรุป Weekly Competitor Intelligence Brief:\n"
                "1. สถานะตลาดสุขภัณฑ์ไทยสัปดาห์นี้\n"
                "2. ช่องโอกาสที่ CERAFIELD ควรเน้น\n"
                "3. คำแนะนำ positioning 1 ข้อสำหรับทีมขาย"
            )},
        ]
        resp = await create_completion(messages)
        brief = resp.choices[0].message.content or ""

        message = (
            f"Intelligence Agent — Weekly Brief {today.strftime('%d/%m/%Y')}\n\n"
            f"{brief}"
        )
        await push_text(settings.tony_line_user_id, message)
        logger.info("Intelligence Agent sent weekly brief")

    except Exception as e:
        logger.error("Intelligence Agent error: %s", type(e).__name__)
