"""Tests for admin_service — tony TR / RP / EM commands."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from app.services.admin_service import parse_admin_command, handle_tony_admin, SKILLS_DIR


# ── parse_admin_command ───────────────────────────────────────────────────────

class TestParseAdminCommand:
    def test_tony_tr(self):
        assert parse_admin_command("tony TR hello world") == ("TR", "hello world")

    def test_tony_rp(self):
        assert parse_admin_command("tony RP สวัสดีครับ") == ("RP", "สวัสดีครับ")

    def test_tony_em(self):
        assert parse_admin_command("tony EM From: test@example.com") == ("EM", "From: test@example.com")

    def test_case_insensitive(self):
        assert parse_admin_command("Tony tr some text")[0] == "TR"
        assert parse_admin_command("TONY TR some text")[0] == "TR"
        assert parse_admin_command("tony tr some text")[0] == "TR"

    def test_no_content(self):
        cmd, content = parse_admin_command("tony TR")
        assert cmd == "TR"
        assert content == ""

    def test_not_admin_command(self):
        assert parse_admin_command("tony qt") == (None, None)
        assert parse_admin_command("สวัสดีครับ") == (None, None)
        assert parse_admin_command("/quote Customer, CF-13022 x5") == (None, None)
        assert parse_admin_command("tony") == (None, None)

    def test_multiline_content(self):
        text = "tony EM From: john@hotel.com\nSubject: Quotation\nBody here"
        cmd, content = parse_admin_command(text)
        assert cmd == "EM"
        assert "From: john@hotel.com" in content
        assert "Subject: Quotation" in content

    def test_content_with_thai_units(self):
        cmd, content = parse_admin_command("tony TR CF-13022 5 ชิ้น เข้าวันไหน")
        assert cmd == "TR"
        assert "CF-13022 5 ชิ้น" in content


# ── handle_tony_admin ─────────────────────────────────────────────────────────

class TestHandleTonyAdmin:
    @pytest.mark.asyncio
    async def test_returns_none_for_non_admin(self):
        result = await handle_tony_admin("สวัสดีครับ")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_tony_qt(self):
        result = await handle_tony_admin("tony qt")
        assert result is None

    @pytest.mark.asyncio
    async def test_usage_hint_when_no_content_tr(self):
        result = await handle_tony_admin("tony TR")
        assert result is not None
        assert "TR" in result
        assert "tony TR" in result

    @pytest.mark.asyncio
    async def test_usage_hint_when_no_content_rp(self):
        result = await handle_tony_admin("tony RP")
        assert result is not None
        assert "RP" in result

    @pytest.mark.asyncio
    async def test_usage_hint_when_no_content_em(self):
        result = await handle_tony_admin("tony EM")
        assert result is not None
        assert "EM" in result

    @pytest.mark.asyncio
    async def test_tr_calls_api_with_skill_prompt(self):
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_TR", "TRANSLATE SKILL PROMPT"):
            mock_chat.return_value = "คำแปลภาษาไทย"
            result = await handle_tony_admin("tony TR Hello world")
            assert result == "คำแปลภาษาไทย"
            call_args = mock_chat.call_args[0][0]
            assert call_args[0]["role"] == "system"
            assert call_args[0]["content"] == "TRANSLATE SKILL PROMPT"
            assert "Hello world" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_rp_calls_api_with_skill_prompt(self):
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_RP", "REPLY SKILL PROMPT"):
            mock_chat.return_value = "Draft reply here"
            result = await handle_tony_admin("tony RP ลูกค้าถามราคา")
            assert result == "Draft reply here"
            call_args = mock_chat.call_args[0][0]
            assert call_args[0]["content"] == "REPLY SKILL PROMPT"
            assert "ลูกค้าถามราคา" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_em_calls_api_with_skill_prompt(self):
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_EM", "EMAIL SKILL PROMPT"):
            mock_chat.return_value = "Draft email reply"
            result = await handle_tony_admin("tony EM From: test@example.com")
            assert result == "Draft email reply"
            call_args = mock_chat.call_args[0][0]
            assert call_args[0]["content"] == "EMAIL SKILL PROMPT"

    @pytest.mark.asyncio
    async def test_trims_long_reply(self):
        long_reply = "x" * 5000
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_TR", "some prompt"):
            mock_chat.return_value = long_reply
            result = await handle_tony_admin("tony TR some text")
            assert len(result) <= 4900
            assert "ตัดที่ 4800" in result

    @pytest.mark.asyncio
    async def test_missing_skill_file_returns_error(self):
        with patch("app.services.admin_service.SKILL_TR", ""):
            result = await handle_tony_admin("tony TR some text")
            assert "❌" in result
            assert "skill file" in result

    @pytest.mark.asyncio
    async def test_api_error_returns_friendly_message(self):
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_TR", "some prompt"):
            mock_chat.side_effect = RuntimeError("connection timeout")
            result = await handle_tony_admin("tony TR some text")
            assert "❌" in result
            assert "RuntimeError" in result

    @pytest.mark.asyncio
    async def test_case_insensitive_command(self):
        with patch("app.services.admin_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
             patch("app.services.admin_service.SKILL_TR", "prompt"):
            mock_chat.return_value = "translation"
            result = await handle_tony_admin("Tony tr hello")
            assert result == "translation"


# ── skills/ files exist ───────────────────────────────────────────────────────

class TestSkillFilesExist:
    def test_skills_directory_exists(self):
        assert SKILLS_DIR.exists(), f"skills/ directory not found at {SKILLS_DIR}"

    def test_translate_skill_exists(self):
        assert (SKILLS_DIR / "แปล.md").exists()

    def test_reply_skill_exists(self):
        assert (SKILLS_DIR / "ตอบลูกค้า.md").exists()

    def test_email_skill_exists(self):
        assert (SKILLS_DIR / "ตอบอีเมล.md").exists()

    def test_skills_not_empty(self):
        for fname in ["แปล.md", "ตอบลูกค้า.md", "ตอบอีเมล.md"]:
            content = (SKILLS_DIR / fname).read_text(encoding="utf-8")
            assert len(content) > 100, f"{fname} appears empty or too short"
