import logging
import time
from functools import lru_cache

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.config import get_settings
from app.core.ai_engine import get_ai_reply
from app.limiter import limiter
from app.memory.store import get_store
from app.services.line_service import reply_catalog, reply_company_profile, reply_text
from app.services.quote_service import create_quotation, parse_quote_command
from app.services.sheets_service import log_line_message

logger = logging.getLogger(__name__)
router = APIRouter()


@lru_cache
def _get_parser() -> WebhookParser:
    return WebhookParser(get_settings().line_channel_secret)


async def _handle_message(user_id: str, user_text: str, reply_token: str) -> None:
    """Background task: enforce daily limit, call OpenAI, and send LINE reply."""
    settings = get_settings()
    store = get_store()

    usage = await store.get_daily_usage(user_id)
    if usage >= settings.daily_message_limit:
        try:
            await reply_text(
                reply_token,
                f"You've reached your daily limit of {settings.daily_message_limit} messages. Please try again tomorrow!",
            )
        except Exception:
            pass
        return

    await store.increment_daily_usage(user_id)

    try:
        t0 = time.monotonic()

        if user_text.strip().lower().startswith("/quote"):
            parsed = parse_quote_command(user_text)
            if not parsed or not parsed.get("items"):
                await reply_text(reply_token, "รูปแบบคำสั่ง: /quote ชื่อลูกค้า [/ โปรเจกต์], SKU x จำนวน\nตัวอย่าง: /quote Holiday Inn / ห้อง 201, CF-13022 x10, CF-600 x5")
                return
            result = await create_quotation(parsed["customer"], parsed["project"], parsed["items"])
            response_ms = int((time.monotonic() - t0) * 1000)
            lines = "\n".join(
                f"  {it['sku']} x{it['qty']}  {it['amount']:,.0f} บาท"
                for it in result["items"]
            )
            drive_line = f"\nPDF: {result['drive_url']}" if result.get("drive_url") else "\n(PDF อัพโหลด Drive ไม่สำเร็จ — ตรวจสอบ log)"
            reply = (
                f"ใบเสนอราคา {result['qt_no']}\n"
                f"ลูกค้า: {result['customer']}"
                + (f"\nโปรเจกต์: {result['project']}" if result.get("project") else "")
                + f"\n\n{lines}\n\n"
                f"Subtotal: {result['subtotal']:,.0f} บาท\n"
                f"VAT 7%:  {result['vat']:,.0f} บาท\n"
                f"รวม:     {result['total']:,.0f} บาท"
                f"{drive_line}"
            )
            await reply_text(reply_token, reply)
            await log_line_message(user_id, user_text, f"[QUOTE {result['qt_no']}]", response_ms)
            return

        reply = await get_ai_reply(user_id, user_text)
        response_ms = int((time.monotonic() - t0) * 1000)

        if reply.strip() == "[CATALOG]":
            await reply_catalog(reply_token)
            await log_line_message(user_id, user_text, "[CATALOG SENT]", response_ms)
        elif reply.strip() == "[PROFILE]":
            await reply_company_profile(reply_token)
            await log_line_message(user_id, user_text, "[PROFILE SENT]", response_ms)
        else:
            await reply_text(reply_token, reply)
            await log_line_message(user_id, user_text, reply, response_ms)
    except Exception as e:
        logger.error("Failed to handle message from %s...: %s", user_id[:8], type(e).__name__)
        try:
            await reply_text(reply_token, "Sorry, something went wrong. Please try again.")
        except Exception:
            pass


@router.post("/callback")
@limiter.limit("60/minute")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None, alias="X-Line-Signature"),
):
    body = await request.body()

    if len(body) > 1_000_000:
        raise HTTPException(status_code=413, detail="Payload too large")

    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body_text = body.decode("utf-8")
    try:
        events = _get_parser().parse(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error("Webhook parse error: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="Webhook processing error")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            background_tasks.add_task(
                _handle_message,
                event.source.user_id,
                event.message.text,
                event.reply_token,
            )

    # Acknowledge LINE immediately — reply is sent asynchronously
    return {"status": "ok"}
