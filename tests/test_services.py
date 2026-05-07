import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


@pytest.mark.asyncio
async def test_chat_completion_success():
    from app.services.openai_service import chat_completion

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "great answer"

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.openai_service.get_client", return_value=mock_client):
        result = await chat_completion([{"role": "user", "content": "hi"}])

    assert result == "great answer"


@pytest.mark.asyncio
async def test_chat_completion_retries_on_rate_limit():
    from openai import RateLimitError
    from app.services.openai_service import chat_completion

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "retried ok"

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    rate_err = RateLimitError(
        "rate limited",
        response=httpx.Response(429, request=req),
        body=None,
    )

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[rate_err, mock_response]
    )

    with patch("app.services.openai_service.get_client", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await chat_completion([{"role": "user", "content": "hi"}])

    assert result == "retried ok"
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_line_reply_text_calls_api():
    from app.services.line_service import reply_text

    mock_client = AsyncMock()
    mock_client.reply_message = AsyncMock()

    with patch("app.services.line_service.get_line_client", return_value=mock_client):
        await reply_text("reply-token-123", "Hello LINE user!")

    mock_client.reply_message.assert_called_once()
    req = mock_client.reply_message.call_args[0][0]
    assert req.reply_token == "reply-token-123"
    assert req.messages[0].text == "Hello LINE user!"
