import logging
from functools import lru_cache

from fastapi import APIRouter, Header, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.config import get_settings
from app.core.ai_engine import get_ai_reply
from app.services.line_service import reply_text

logger = logging.getLogger(__name__)
router = APIRouter()


@lru_cache
def _get_parser() -> WebhookParser:
    return WebhookParser(get_settings().line_channel_secret)


@router.post("/callback")
async def callback(
    request: Request,
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
            user_id = event.source.user_id
            user_text = event.message.text
            reply_token = event.reply_token

            try:
                reply = await get_ai_reply(user_id, user_text)
                await reply_text(reply_token, reply)
            except Exception as e:
                logger.error("Failed to handle message from %s...: %s", user_id[:8], type(e).__name__)
                try:
                    await reply_text(reply_token, "Sorry, something went wrong. Please try again.")
                except Exception:
                    pass

    return {"status": "ok"}
