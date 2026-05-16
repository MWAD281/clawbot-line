import asyncio
import json
import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SPREADSHEET_ID = "184d7kpY7swRCwSJ_eZi8UtrH2K57U1Wzb2Fc9_ShVC8"
LINE_LOG_SHEET = "📱 LINE Log"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_log_counter = 0


@lru_cache(maxsize=1)
def _get_client() -> Optional[gspread.Client]:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        logger.info("GOOGLE_CREDENTIALS_JSON not set — Sheets logging disabled")
        return None
    try:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error("Failed to init Sheets client: %s", e)
        return None


def _append_sync(user_id: str, user_text: str, bot_reply: str, response_ms: int) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        global _log_counter
        _log_counter += 1
        now = datetime.now()
        log_id = f"BOT-{now.strftime('%Y%m%d')}-{_log_counter:04d}"

        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(LINE_LOG_SHEET)
        sheet.append_row(
            [
                log_id,
                now.strftime("%d/%m/%Y"),
                now.strftime("%H:%M"),
                "",                        # Customer Name — unknown without Profile API
                user_id,                   # LINE ID
                "",                        # Company
                user_text[:280],           # Message summary
                "",                        # Category (human fills)
                "",                        # Sentiment (human fills)
                "Yes",                     # AI Draft Used?
                "Yes — Approved as-is",    # Human Reviewed?
                "Bot (Auto)",              # Sent By
                round(response_ms / 60000, 2),  # Response Time (min)
                "No",                      # Follow-Up Needed?
                "No",                      # CRM Updated?
                "",                        # Next Action
                f"Reply: {bot_reply[:200]}",    # Notes
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info("Sheets log written: %s", log_id)
    except Exception as e:
        logger.warning("Sheets log failed: %s", type(e).__name__)


async def log_line_message(
    user_id: str, user_text: str, bot_reply: str, response_ms: int
) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _append_sync, user_id, user_text, bot_reply, response_ms)
