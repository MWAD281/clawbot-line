import asyncio
import logging
from typing import List, Dict, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat_completion(messages: List[Dict[str, str]], max_retries: int = 3) -> str:
    client = get_client()

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
            )
            return response.choices[0].message.content or ""
        except RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait)
        except APITimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    raise RuntimeError("OpenAI request failed after all retries")
