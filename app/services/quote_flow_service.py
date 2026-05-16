"""
Multi-step LINE quote flow — retail and project paths.

State stored per user_id in ConversationStore (Redis / in-memory).
Returns FlowReply(text, quick_reply) so webhook can choose reply_text or reply_quick.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.quote_service import PROJECT_PRICE_LIST, create_quotation, parse_quote_command

logger = logging.getLogger(__name__)

CANCEL_WORDS = {"ยกเลิก", "cancel", "ออก", "หยุด", "exit"}

_HINT_RETAIL = (
    "รหัสสินค้าและราคาปลีก (บาท):\n"
    "CF-2495 8,800  |  CF-13022 10,800  |  CF-2493 8,580\n"
    "CF-12014 22,880  |  CF-12016 23,880\n"
    "CF-15001 15,880  |  CF-15005 10,800\n"
    "CF-4037 12,800  |  CF-U622 15,280\n"
    "CF-600 1,980  |  CF-C425 21,800  |  CF-B425 18,880\n"
    "CF-18004 12,800  |  CF-2138 3,080  |  CF-S01 850"
)

_HINT_PROJECT = (
    "รหัสสินค้า — ราคาปลีก / ราคาโปรเจค:\n"
    "CF-13022  10,800 / 5,880 (100+)\n"
    "CF-2493   8,580  / 4,880 (100+)\n"
    "CF-2495   8,800  / 4,980 (100+)\n"
    "CF-12014  22,880 / 12,880 (100+)\n"
    "CF-12016  23,880 / 16,880 (100+)\n"
    "CF-15001  15,880 / 9,580 (100+)\n"
    "CF-15005  10,800 / 7,560 (100+)\n"
    "CF-4037   12,800 / 5,280 (100+)\n"
    "CF-600    1,980  / 1,380 (100+)\n"
    "CF-U622   15,280 / 10,280 (20+)\n"
    "CF-U668   — / 13,860 (20+)\n"
    "CF-C425 21,800  |  CF-B425 18,880  |  CF-18004 12,800"
)


@dataclass
class FlowReply:
    text: str
    quick_reply: Optional[List[str]] = field(default=None)


def _preview_items(items: list) -> str:
    return "\n".join(
        f"  {i['sku']} x{i['qty']}  {i['unit_price']:,.0f} บาท/ชิ้น  รวม {i['amount']:,.0f} บาท"
        for i in items
    )


def _subtotal_preview(items: list) -> float:
    return sum(i["amount"] for i in items)


def _confirm_text(state: dict, items: list) -> str:
    subtotal = _subtotal_preview(items)
    vat = round(subtotal * 0.07, 2)
    total = round(subtotal + vat, 2)
    lines = _preview_items(items)
    tax_line = f"\nเลขผู้เสียภาษี: {state['tax_id']}" if state.get("tax_id") else ""
    proj_line = f"\nโปรเจค: {state['project']}" if state.get("project") else ""
    return (
        f"สรุปก่อนสร้าง PDF:\n"
        f"ลูกค้า: {state['customer']}{tax_line}{proj_line}\n\n"
        f"{lines}\n\n"
        f"Subtotal: {subtotal:,.0f} บาท\n"
        f"VAT 7%:   {vat:,.0f} บาท\n"
        f"รวม:      {total:,.0f} บาท\n\n"
        f"ยืนยันสร้าง PDF ได้เลยคะ"
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
        + (f"\nโปรเจค: {result['project']}" if result.get("project") else "")
        + f"\n\n{lines}\n\n"
        f"Subtotal: {result['subtotal']:,.0f} บาท\n"
        f"VAT 7%:   {result['vat']:,.0f} บาท\n"
        f"รวม:      {result['total']:,.0f} บาท"
        f"{drive_line}"
    )


async def start_quote_flow(user_id: str, store) -> FlowReply:
    await store.set_quote_flow(user_id, {"step": "type_select"})
    return FlowReply(
        text="ใบเสนอราคาสำหรับอะไรคะ? (พิมพ์ ยกเลิก เพื่อออก)",
        quick_reply=["ใช้ส่วนตัว", "งานโปรเจค"],
    )


async def handle_quote_flow(user_id: str, text: str, store) -> Optional[FlowReply]:
    """Returns FlowReply if user is in an active flow, None otherwise."""
    state = await store.get_quote_flow(user_id)
    if state is None:
        return None

    t = text.strip()

    if t.lower() in CANCEL_WORDS:
        await store.clear_quote_flow(user_id)
        return FlowReply(text="ยกเลิกการทำใบเสนอราคาแล้วค่ะ")

    step = state.get("step")

    # ── Type selection ──────────────────────────────────────────────
    if step == "type_select":
        if "ส่วนตัว" in t or "ปลีก" in t or t == "ซื้อใช้ส่วนตัว":
            state.update({"step": "retail_name", "quote_type": "retail",
                          "tax_id": "", "project": ""})
            await store.set_quote_flow(user_id, state)
            return FlowReply(text="ชื่อ-นามสกุลคะ?")
        if "โปรเจค" in t or "ธุรกิจ" in t or "project" in t.lower():
            state.update({"step": "project_company", "quote_type": "project"})
            await store.set_quote_flow(user_id, state)
            return FlowReply(
                text="ชื่อบริษัท และเลขผู้เสียภาษี (ถ้ามี) คะ?\n"
                     "ตัวอย่าง: บริษัท ABC จำกัด / 1234567890123\n"
                     "หรือพิมพ์ชื่อบริษัทเพียงอย่างเดียวก็ได้ค่ะ",
            )
        return FlowReply(
            text="กรุณาเลือกประเภทค่ะ",
            quick_reply=["ใช้ส่วนตัว", "งานโปรเจค"],
        )

    # ── Retail path ─────────────────────────────────────────────────
    if step == "retail_name":
        state["customer"] = t
        state["step"] = "retail_products"
        await store.set_quote_flow(user_id, state)
        return FlowReply(
            text=f"สินค้าที่ต้องการคะ เช่น CF-13022 x2, CF-600 x1\n\n{_HINT_RETAIL}"
        )

    if step == "retail_products":
        result = _parse_products(t, state)
        if isinstance(result, FlowReply):
            return result
        items = result
        state["items"] = items
        state["step"] = "retail_confirm"
        await store.set_quote_flow(user_id, state)
        return FlowReply(
            text=_confirm_text(state, items),
            quick_reply=["ยืนยัน", "แก้ไขสินค้า"],
        )

    if step == "retail_confirm":
        return await _handle_confirm(t, state, "retail_products", user_id, store)

    # ── Project path ─────────────────────────────────────────────────
    if step == "project_company":
        if "/" in t:
            company, tax_id = t.split("/", 1)
            state["customer"] = company.strip()
            state["tax_id"] = tax_id.strip()
        else:
            state["customer"] = t
            state["tax_id"] = ""
        state["step"] = "project_name"
        await store.set_quote_flow(user_id, state)
        return FlowReply(text="ชื่อโปรเจคคะ?")

    if step == "project_name":
        state["project"] = t
        state["step"] = "project_products"
        await store.set_quote_flow(user_id, state)
        return FlowReply(
            text=f"สินค้าที่ต้องการคะ เช่น CF-13022 x100, CF-600 x20\n\n{_HINT_PROJECT}"
        )

    if step == "project_products":
        result = _parse_products(t, state)
        if isinstance(result, FlowReply):
            return result
        items = result
        state["items"] = items
        state["step"] = "project_confirm"
        await store.set_quote_flow(user_id, state)
        return FlowReply(
            text=_confirm_text(state, items),
            quick_reply=["ยืนยัน", "แก้ไขสินค้า"],
        )

    if step == "project_confirm":
        return await _handle_confirm(t, state, "project_products", user_id, store)

    await store.clear_quote_flow(user_id)
    return None


def _parse_products(text: str, state: dict):
    """Returns items list on success, FlowReply on error."""
    hint = _HINT_PROJECT if state.get("quote_type") == "project" else _HINT_RETAIL
    parsed = parse_quote_command(f"/quote dummy, {text}")
    items = parsed.get("items", [])
    if not items:
        return FlowReply(text=f"ไม่พบรหัสสินค้าค่ะ กรุณาระบุใหม่\n\n{hint}")
    unknown = [i["sku"] for i in items if i["unit_price"] == 0 and i["sku"] not in PROJECT_PRICE_LIST]
    if unknown:
        return FlowReply(text=f"ไม่พบรหัส: {', '.join(unknown)}\nกรุณาตรวจสอบและลองใหม่ค่ะ")
    return items


async def _handle_confirm(text: str, state: dict, products_step: str, user_id: str, store) -> FlowReply:
    if text in ("ยืนยัน",):
        await store.clear_quote_flow(user_id)
        try:
            items = state.get("items", [])
            notes = f"เลขผู้เสียภาษี: {state['tax_id']}" if state.get("tax_id") else ""
            result = await create_quotation(state["customer"], state.get("project", ""), items, notes)
            return FlowReply(text=_format_result(result))
        except Exception as e:
            logger.error("Quote flow create_quotation error: %s", e)
            return FlowReply(text="เกิดข้อผิดพลาดในการสร้างใบเสนอราคา กรุณาลองใหม่ค่ะ")
    if text in ("แก้ไขสินค้า",):
        hint = _HINT_PROJECT if state.get("quote_type") == "project" else _HINT_RETAIL
        state["step"] = products_step
        await store.set_quote_flow(user_id, state)
        return FlowReply(text=f"พิมพ์สินค้าใหม่ได้เลยคะ\n\n{hint}")
    return FlowReply(
        text="กรุณากดปุ่มค่ะ",
        quick_reply=["ยืนยัน", "แก้ไขสินค้า"],
    )
