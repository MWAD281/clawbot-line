import hashlib
import hmac
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_signature(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


@pytest.fixture
def client(mock_openai_reply, mock_line_reply):
    """TestClient with AI and LINE replies mocked out."""
    from main import app
    with TestClient(app) as c:
        yield c


def _text_event_body(user_id: str = "U12345678", text: str = "Hello") -> bytes:
    return json.dumps({
        "destination": "Utest",
        "events": [{
            "type": "message",
            "mode": "active",
            "timestamp": 1625665161000,
            "source": {"type": "user", "userId": user_id},
            "webhookEventId": "evt1",
            "deliveryContext": {"isRedelivery": False},
            "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
            "message": {"id": "msg1", "type": "text", "quoteToken": "q1", "text": text},
        }],
    }).encode()


def _signed_post(client, body: bytes, secret: str):
    sig = _make_signature(body, secret)
    return client.post("/callback", content=body, headers={"X-Line-Signature": sig})


def test_valid_message_returns_200(client):
    from app.config import get_settings
    body = _text_event_body()
    resp = _signed_post(client, body, get_settings().line_channel_secret)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_missing_signature_returns_400(client):
    body = _text_event_body()
    resp = client.post("/callback", content=body)
    assert resp.status_code == 400


def test_invalid_signature_returns_400(client):
    body = _text_event_body()
    resp = client.post("/callback", content=body, headers={"X-Line-Signature": "badsig=="})
    assert resp.status_code == 400


def test_oversized_body_returns_413(client):
    body = b"x" * 1_000_001
    resp = client.post("/callback", content=body, headers={"X-Line-Signature": "sig"})
    assert resp.status_code == 413


def test_ai_failure_sends_fallback(mock_line_reply):
    """When AI raises, background task must send the fallback reply to LINE."""
    with patch("app.api.webhook.get_ai_reply", new_callable=AsyncMock) as bad_ai:
        bad_ai.side_effect = RuntimeError("OpenAI down")
        from main import app
        with TestClient(app) as c:
            from app.config import get_settings
            body = _text_event_body()
            resp = _signed_post(c, body, get_settings().line_channel_secret)

    assert resp.status_code == 200
    assert mock_line_reply.called
    args = mock_line_reply.call_args[0]
    assert "wrong" in args[1].lower() or "sorry" in args[1].lower()


def test_daily_limit_sends_limit_message(mock_line_reply):
    """When daily limit is reached, send a limit message and skip the AI call."""
    mock_store = MagicMock()
    mock_store.get_daily_usage = AsyncMock(return_value=100)
    mock_store.increment_daily_usage = AsyncMock(return_value=101)

    with patch("app.api.webhook.get_store", return_value=mock_store), \
         patch("app.api.webhook.get_ai_reply", new_callable=AsyncMock) as mock_ai:
        from main import app
        with TestClient(app) as c:
            from app.config import get_settings
            body = _text_event_body()
            resp = _signed_post(c, body, get_settings().line_channel_secret)

    assert resp.status_code == 200
    assert mock_line_reply.called
    args = mock_line_reply.call_args[0]
    assert "limit" in args[1].lower()
    mock_ai.assert_not_called()
