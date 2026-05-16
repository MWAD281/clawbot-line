import logging
from typing import Optional

from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    FlexMessage,
    ReplyMessageRequest,
    TextMessage,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_api_client: Optional[AsyncApiClient] = None
_messaging_api: Optional[AsyncMessagingApi] = None

CATALOG_URL = "https://drive.google.com/file/d/1ffCXQExsfNg_GpVH9gkuVblHzsntf8Qv/view?usp=sharing"
PROFILE_URL = "https://drive.google.com/file/d/1kSp7eDJdloj3imd1uM7wjKr74-IvaBrh/view?usp=sharing"


def get_line_client() -> AsyncMessagingApi:
    global _api_client, _messaging_api
    if _messaging_api is None:
        configuration = Configuration(access_token=get_settings().line_channel_access_token)
        _api_client = AsyncApiClient(configuration)
        _messaging_api = AsyncMessagingApi(_api_client)
    return _messaging_api


async def reply_text(reply_token: str, text: str) -> None:
    client = get_line_client()
    try:
        await client.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)],
            )
        )
    except Exception as e:
        logger.error("Failed to send LINE reply: %s", type(e).__name__)
        raise


def _doc_flex(title: str, subtitle: str, pages: str, url: str, btn_label: str) -> dict:
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#1C2B5E",
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "CERAFIELD", "color": "#F5B800",
                 "size": "xs", "weight": "bold"},
                {"type": "text", "text": title, "color": "#FFFFFF",
                 "size": "lg", "weight": "bold", "wrap": True},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": subtitle, "color": "#444444",
                 "size": "sm", "wrap": True},
                {"type": "text", "text": pages, "color": "#888888", "size": "xs"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#1C2B5E",
                    "action": {"type": "uri", "label": btn_label, "uri": url},
                }
            ],
        },
    }


async def reply_catalog(reply_token: str) -> None:
    text = (
        "📚 CERAFIELD Product Catalog 2026\n"
        "รวมสุขภัณฑ์ทุกซีรีส์ — Core, C-Heritage, Lagoons, FLUSSO\n\n"
        f"🔗 {CATALOG_URL}"
    )
    await reply_text(reply_token, text)


async def reply_company_profile(reply_token: str) -> None:
    text = (
        "🏢 CERAFIELD Company Profile 2026\n"
        "CERAFIELD INTERNATIONAL (THAILAND) CO., LTD.\n\n"
        f"🔗 {PROFILE_URL}"
    )
    await reply_text(reply_token, text)
