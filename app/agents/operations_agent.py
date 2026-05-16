import logging
from datetime import date

from app.config import get_settings
from app.services.sheets_service import get_crm_sheet
from app.services.line_service import push_text

logger = logging.getLogger(__name__)

THRESHOLDS = {
    "CF-2495": 10, "CF-13022": 10, "CF-2493": 10, "CF-2507": 10,
    "CF-12014": 8, "CF-12016": 8, "CF-15001": 8, "CF-15005": 8,
    "CF-4037": 5, "CF-U622": 5,
    "CF-600": 20, "CF-C425": 5, "CF-B425": 5,
    "CF-18004": 5, "CF-2138": 10, "CF-S01": 20,
}


async def run_operations_agent() -> None:
    settings = get_settings()
    if not settings.tony_line_user_id:
        logger.warning("TONY_LINE_USER_ID not set — skipping Operations Agent")
        return

    try:
        ws = get_crm_sheet("📦 Inventory")
        if ws is None:
            logger.warning("Operations Agent: cannot access Inventory sheet")
            return

        rows = ws.get_all_records()
        alerts = []

        for row in rows:
            sku = str(row.get("SKU", "")).strip()
            last_updated = str(row.get("Last Updated", "")).strip()
            if not last_updated:
                continue  # stock not yet received — skip alert
            try:
                stock = int(row.get("Stock", 0))
            except (ValueError, TypeError):
                continue
            threshold = THRESHOLDS.get(sku, 5)
            if stock <= threshold:
                alerts.append(f"  {sku}: เหลือ {stock} ชิ้น (ควรสั่งเมื่อ ≤{threshold})")

        today = date.today()
        if not alerts:
            logger.info("Operations Agent: all stock levels OK")
            return

        message = (
            f"Operations Agent — Stock Alert {today.strftime('%d/%m/%Y')}\n\n"
            "สินค้าที่ต้องติดตาม:\n" + "\n".join(alerts) + "\n\n"
            "กรุณาตรวจสอบและสั่งเพิ่มจากโรงงานค่ะ"
        )
        await push_text(settings.tony_line_user_id, message)
        logger.info("Operations Agent sent stock alert for %d SKUs", len(alerts))

    except Exception as e:
        logger.error("Operations Agent error: %s", type(e).__name__)
