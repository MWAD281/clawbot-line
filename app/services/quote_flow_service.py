"""
Multi-step LINE quote flow.
State machine stored per user_id; driven by webhook _handle_message.
"""
import logging
from typing import Optional

from app.services.quote_service import create_quotation, parse_quote_command

logger = logging.getLogger(__name__)

CANCEL_WORDS = {"ยกเลิก", "cancel", "ออก", "หยุด", "exit"}

_PRODUCT_HINT = (
    "รหัสสินค้าและราคา (บาท):\n"
    "CF-2495 8,800  |  CF-13022 10,800  |  CF-2493 8,580  |  CF-2507 8,580\n"
    "CF-12014 22,880  |  CF-12016 23,880\n"
    "CF-15001 15,880  |  CF-15005 10,800\n"
    "CF-4037 12,800  |  CF-U622 15,280\n"
    "CF-600 1,980  |  CF-C425 21,800  |  CF-B425 18,880\n"
    "CF-18004 12,800  |  CF-2138 3,080  |  CF-S01 850"
)


def _format_result(result: dict) -> str:
    lines = "\n".join(
        f"  {i['sku']} x{i['qty']}  {i['amount']:,.0f} บาท"
        for i in result["items"]
    )
    drive_line = (
        f"\nPDF: {result['drive_url']}"
        if result.get("drive_url")
        else f"\nPDF error: {result.get('drive_error', 'unknown')}"
    )
    return (
        f"ใบเสนอราคา {result['qt_no']}\n"
        f"ลูกค้า: {result['customer']}"
        + (f"\nโปรเจกต์: {result['project']}" if result.get("project") else "")
        + f"\n\n{lines}\n\n"
        f"Subtotal: {result['subtotal']:,.0f} บาท\n"
        f"VAT 7%:   {result['vat']:,.0f} บาท\n"
        f"รวม:      {result['total']:,.0f} บาท"
        f"{drive_line}"
    )


async def start_quote_flow(user_id: str, store) -> str:
    await store.set_quote_flow(user_id, {"step": "asking_customer"})
    return "ชื่อลูกค้าหรือบริษัทคะ? (พิมพ์ ยกเลิก เพื่อออก)"


async def handle_quote_flow(user_id: str, text: str, store) -> Optional[str]:
    """
    Returns reply string if the user is in a quote flow, None otherwise.
    """
    state = await store.get_quote_flow(user_id)
    if state is None:
        return None

    if text.strip().lower() in CANCEL_WORDS:
        await store.clear_quote_flow(user_id)
        return "ยกเลิกการทำใบเสนอราคาแล้วค่ะ"

    step = state.get("step")

    if step == "asking_customer":
        state["customer"] = text.strip()
        state["step"] = "asking_project"
        await store.set_quote_flow(user_id, state)
        return "โปรเจกต์หรืองานอะไรคะ? (พิมพ์ - ถ้าไม่มี)"

    if step == "asking_project":
        state["project"] = "" if text.strip() == "-" else text.strip()
        state["step"] = "asking_products"
        await store.set_quote_flow(user_id, state)
        return f"สินค้าที่ต้องการคะ เช่น CF-13022 x10, CF-600 x5\n\n{_PRODUCT_HINT}"

    if step == "asking_products":
        parsed = parse_quote_command(f"/quote dummy, {text.strip()}")
        items = parsed.get("items", [])
        if not items:
            return f"ไม่พบรหัสสินค้าค่ะ กรุณาระบุใหม่ เช่น CF-13022 x10\n\n{_PRODUCT_HINT}"

        unknown = [i["sku"] for i in items if i["unit_price"] == 0]
        if unknown:
            return f"ไม่พบรหัส: {', '.join(unknown)}\nกรุณาตรวจสอบและลองใหม่ค่ะ"

        await store.clear_quote_flow(user_id)
        try:
            result = await create_quotation(state["customer"], state["project"], items)
            return _format_result(result)
        except Exception as e:
            logger.error("Quote flow create_quotation error: %s", e)
            return "เกิดข้อผิดพลาดในการสร้างใบเสนอราคา กรุณาลองใหม่ค่ะ"

    # Unknown step — reset
    await store.clear_quote_flow(user_id)
    return None
