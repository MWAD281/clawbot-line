import os
from unittest.mock import MagicMock, patch

import pytest


def test_log_skipped_when_no_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    from app.services import sheets_service
    sheets_service._get_client.cache_clear()
    client = sheets_service._get_client()
    assert client is None


def test_log_skipped_on_bad_credentials(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", "not-valid-json")
    from app.services import sheets_service
    sheets_service._get_client.cache_clear()
    client = sheets_service._get_client()
    assert client is None
    sheets_service._get_client.cache_clear()


def test_append_sync_noop_without_client(monkeypatch):
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    from app.services import sheets_service
    sheets_service._get_client.cache_clear()
    # Should not raise
    sheets_service._append_sync("U123", "hello", "world", 1000)
    sheets_service._get_client.cache_clear()


@pytest.mark.asyncio
async def test_log_line_message_noop_without_client(monkeypatch):
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    from app.services import sheets_service
    sheets_service._get_client.cache_clear()
    # Should not raise
    await sheets_service.log_line_message("U123", "hello", "world", 1000)
    sheets_service._get_client.cache_clear()
