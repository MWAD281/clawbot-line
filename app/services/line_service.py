import logging
from typing import Optional

from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_api_client: Optional[AsyncApiClient] = None
_messaging_api: Optional[AsyncMessagingApi] = None


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
