import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_reply_stored_in_history(mock_openai_reply):
    from app.core.ai_engine import get_ai_reply
    from app.memory.store import get_store

    await get_ai_reply("user1", "Hi")
    history = await get_store().get_history("user1")

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hi"}
    assert history[1] == {"role": "assistant", "content": "Hello from bot"}


@pytest.mark.asyncio
async def test_system_prompt_prepended():
    from app.core.ai_engine import get_ai_reply, SYSTEM_PROMPT

    with patch("app.core.ai_engine.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "ok"
        await get_ai_reply("user2", "test")

    call_messages = mock_chat.call_args[0][0]
    assert call_messages[0] == {"role": "system", "content": SYSTEM_PROMPT}


@pytest.mark.asyncio
async def test_fallback_returned_on_exception():
    from app.core.ai_engine import get_ai_reply, FALLBACK_MESSAGE

    with patch("app.core.ai_engine.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = RuntimeError("API down")
        result = await get_ai_reply("user3", "hello")

    assert result == FALLBACK_MESSAGE


@pytest.mark.asyncio
async def test_history_not_stored_on_failure():
    from app.core.ai_engine import get_ai_reply
    from app.memory.store import get_store

    with patch("app.core.ai_engine.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = RuntimeError("API down")
        await get_ai_reply("user4", "hello")

    history = await get_store().get_history("user4")
    roles = [m["role"] for m in history]
    # User message is added before the AI call; no assistant reply should exist on failure
    assert "assistant" not in roles
