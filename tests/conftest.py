import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_completion_response(content: str = "Hello from bot"):
    """Build a minimal ChatCompletion-like mock with finish_reason='stop'."""
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    choice.message.tool_calls = None
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """
    Set env vars so the real Settings() instantiation succeeds in every module
    that holds its own reference to get_settings. Clearing lru_cache ensures
    fresh Settings() reads these env vars instead of returning a stale real value.
    """
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test_secret_that_is_long_enough_32c")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    from app.config import get_settings
    get_settings.cache_clear()

    yield

    from app.config import get_settings
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset module-level singletons so tests don't share state."""
    import app.services.openai_service as ois
    import app.services.line_service as ls
    import app.memory.store as st

    ois._client = None
    ls._api_client = None
    ls._messaging_api = None
    st._store = None

    try:
        from app.api import webhook as wh
        wh._get_parser.cache_clear()
    except Exception:
        pass

    yield

    ois._client = None
    ls._api_client = None
    ls._messaging_api = None
    st._store = None


@pytest.fixture
def mock_line_reply():
    """Patch reply_text at the webhook module where it was imported."""
    with patch("app.api.webhook.reply_text", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_openai_reply():
    """Patch create_completion at the ai_engine module where it was imported."""
    with patch("app.core.ai_engine.create_completion", new_callable=AsyncMock) as mock:
        mock.return_value = _make_completion_response("Hello from bot")
        yield mock
