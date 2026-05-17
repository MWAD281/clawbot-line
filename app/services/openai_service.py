import asyncio
import logging
from typing import List, Dict, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key, timeout=20.0)
    return _client


async def create_completion(messages: list, tools: Optional[list] = None, max_retries: int = 3):
    """Return the raw ChatCompletion response object (with optional tool definitions)."""
    client = get_client()
    settings = get_settings()

    kwargs: dict = {
        "model": settings.openai_model,
        "messages": messages,
        "max_tokens": settings.openai_max_tokens,
    }
    if tools:
        kwargs["tools"] = tools

    for attempt in range(max_retries):
        try:
            return await client.chat.completions.create(**kwargs)
        except RateLimitError:
            wait = 2 ** attempt
            logger.warning("Rate limited, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
            if attempt < max_retries - 1:
                await asyncio.sleep(wait)
        except APITimeoutError:
            logger.warning("Timeout on attempt %d/%d", attempt + 1, max_retries)
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
        except APIError as e:
            logger.error("OpenAI API error: %s", type(e).__name__)
            raise

    raise RuntimeError("OpenAI request failed after all retries")


async def chat_completion(messages: List[Dict[str, str]], max_retries: int = 3) -> str:
    """Convenience wrapper — returns just the text content."""
    response = await create_completion(messages, max_retries=max_retries)
    return response.choices[0].message.content or ""
