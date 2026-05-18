"""Tests for lead_flow_service — 50-99 pcs inquiry capture."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.lead_flow_service import (
    LeadReply,
    handle_lead_flow,
    start_lead_flow,
    _save_lead,
    _notify_admin,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_store(state=None, lead_state=None):
    store = MagicMock()
    store.get_lead_flow = AsyncMock(return_value=lead_state)
    store.set_lead_flow = AsyncMock()
    store.clear_lead_flow = AsyncMock()
    return store


# ── start_lead_flow ───────────────────────────────────────────────────────────

class TestStartLeadFlow:
    @pytest.mark.asyncio
    async def test_sets_collect_step(self):
        store = make_store()
        reply = await start_lead_flow("user123", store)
        store.set_lead_flow.assert_called_once_with("user123", {"step": "collect"})

    @pytest.mark.asyncio
    async def test_returns_form_prompt(self):
        store = make_store()
        reply = await start_lead_flow("user123", store)
        assert isinstance(reply, LeadReply)
        assert "ชื่อ-นามสกุล" in reply.text
        assert "เบอร์โทร" in reply.text
        assert "Email" in reply.text


# ── handle_lead_flow ──────────────────────────────────────────────────────────

class TestHandleLeadFlow:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_flow(self):
        store = make_store(lead_state=None)
        result = await handle_lead_flow("user123", "สวัสดี", store)
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_clears_flow(self):
        store = make_store(lead_state={"step": "collect"})
        for word in ["ยกเลิก", "cancel", "ออก", "หยุด", "exit"]:
            store.get_lead_flow = AsyncMock(return_value={"step": "collect"})
            reply = await handle_lead_flow("user123", word, store)
            assert reply is not None
            assert "ยกเลิก" in reply.text
            store.clear_lead_flow.assert_called()

    @pytest.mark.asyncio
    async def test_collect_step_saves_and_confirms(self):
        store = make_store(lead_state={"step": "collect"})
        info = "ชื่อ: สมชาย\nเบอร์: 0812345678\nEmail: test@test.com"

        with patch("app.services.lead_flow_service._save_lead") as mock_save, \
             patch("app.services.lead_flow_service._notify_admin") as mock_notify:
            reply = await handle_lead_flow("user123", info, store)

        assert reply is not None
        assert "ขอบคุณ" in reply.text
        assert "24 ชั่วโมง" in reply.text
        mock_save.assert_called_once_with("user123", info)
        mock_notify.assert_called_once_with("user123", info)
        store.clear_lead_flow.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_step_clears_flow(self):
        store = make_store(lead_state={"step": "unknown_step"})
        result = await handle_lead_flow("user123", "some text", store)
        assert result is None
        store.clear_lead_flow.assert_called_once()


# ── _save_lead ────────────────────────────────────────────────────────────────

class TestSaveLead:
    def test_saves_to_sheet(self):
        with patch("app.services.lead_flow_service.append_to_sheet") as mock_append:
            _save_lead("user123", "ชื่อ: สมชาย")
            mock_append.assert_called_once()
            args = mock_append.call_args[0]
            assert args[0] == "📋 Leads"
            assert "user123" in args[1]

    def test_truncates_long_text(self):
        long_text = "x" * 1000
        with patch("app.services.lead_flow_service.append_to_sheet") as mock_append:
            _save_lead("user123", long_text)
            row = mock_append.call_args[0][1]
            info_cell = row[3]
            assert len(info_cell) <= 500

    def test_handles_sheets_error_gracefully(self):
        with patch("app.services.lead_flow_service.append_to_sheet", side_effect=Exception("Sheets down")):
            # Should not raise
            _save_lead("user123", "some info")


# ── _notify_admin ─────────────────────────────────────────────────────────────

class TestNotifyAdmin:
    def test_skips_when_no_tony_id(self):
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.tony_line_user_id = ""
            with patch("app.services.lead_flow_service.asyncio.create_task") as mock_task:
                _notify_admin("user123", "lead info")
                mock_task.assert_not_called()

    def test_sends_push_when_tony_id_set(self):
        with patch("app.config.get_settings") as mock_settings, \
             patch("app.services.lead_flow_service.asyncio.create_task") as mock_task, \
             patch("app.services.line_service.push_text", new_callable=AsyncMock):
            mock_settings.return_value.tony_line_user_id = "Uabc123"
            _notify_admin("user456", "lead info")
            mock_task.assert_called_once()

    def test_handles_error_gracefully(self):
        with patch("app.config.get_settings", side_effect=Exception("config error")):
            # Should not raise
            _notify_admin("user123", "lead info")
