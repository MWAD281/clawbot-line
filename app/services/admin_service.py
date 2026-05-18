"""
Admin commands for Tony — tony TR / RP / EM

Reads system prompts from skills/*.md files at startup.
Update a skill: edit the .md file → git push → Render auto-redeploys.

Usage (send from Tony's personal LINE to Cerafield LINE OA):
  tony TR [text] [th/en/zh]      — translate
  tony RP [customer message]     — draft customer reply
  tony EM [paste email content]  — draft email reply
"""
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

from app.services.openai_service import chat_completion

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

LINE_MAX_CHARS = 4800  # LINE hard limit is 5000; leave buffer


# ── Load skills from .md files ────────────────────────────────────────────────

def _load_skill(filename: str) -> str:
    """Read a skill .md file. Returns empty string if not found."""
    path = SKILLS_DIR / filename
    if path.exists():
        content = path.read_text(encoding="utf-8")
        logger.info("Loaded skill: %s (%d chars)", filename, len(content))
        return content
    logger.warning("Skill file not found: %s", path)
    return ""


# Loaded once at import — refreshed on each Render deploy
SKILL_TR = _load_skill("แปล.md")
SKILL_RP = _load_skill("ตอบลูกค้า.md")
SKILL_EM = _load_skill("ตอบอีเมล.md")

# ── Command parsing ───────────────────────────────────────────────────────────

# Matches: "tony TR ...", "tony RP ...", "tony EM ..."  (case-insensitive)
_CMD_RE = re.compile(r'^tony\s+(TR|RP|EM)\b\s*(.*)', re.IGNORECASE | re.DOTALL)


def parse_admin_command(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (cmd_upper, content) or (None, None) if not an admin command.
    cmd_upper is one of: 'TR', 'RP', 'EM'
    """
    m = _CMD_RE.match(text.strip())
    if not m:
        return None, None
    return m.group(1).upper(), m.group(2).strip()


# ── Usage hints ───────────────────────────────────────────────────────────────

_USAGE = {
    "TR": (
        "📖 tony TR — แปลภาษา\n\n"
        "tony TR [ข้อความ]\n"
        "tony TR [ข้อความ] th\n"
        "tony TR [ข้อความ] zh\n"
        "tony TR [ข้อความ] en\n"
        "tony TR [ข้อความ] formal\n\n"
        "ตัวอย่าง:\n"
        "tony TR Wall-hung basin for hotel project th\n"
        "tony TR สินค้าเข้าวันไหนครับ en"
    ),
    "RP": (
        "📖 tony RP — draft reply ลูกค้า\n\n"
        "tony RP [ข้อความลูกค้า]\n"
        "tony RP [ข้อความ] formal\n"
        "tony RP [ข้อความ] short\n\n"
        "ตัวอย่าง:\n"
        "tony RP สวัสดีครับ อยากทราบราคา CF-13022 ครับ"
    ),
    "EM": (
        "📖 tony EM — draft email reply\n\n"
        "tony EM [วางอีเมลต้นฉบับ]\n"
        "tony EM [อีเมล] en\n"
        "tony EM [อีเมล] short\n\n"
        "ตัวอย่าง:\n"
        "tony EM From: john@hotel.com\nSubject: Quotation request..."
    ),
}

# ── Main handler ─────────────────────────────────────────────────────────────

async def handle_tony_admin(text: str) -> Optional[str]:
    """
    Entry point for webhook. Returns reply string or None if not an admin command.
    """
    cmd, content = parse_admin_command(text)
    if cmd is None:
        return None

    # No content → show usage hint
    if not content:
        return _USAGE.get(cmd, f"tony {cmd} [ข้อความ]")

    # Map command → skill + user instruction
    if cmd == "TR":
        skill = SKILL_TR
        user_msg = f"แปลข้อความนี้:\n\n{content}"
    elif cmd == "RP":
        skill = SKILL_RP
        user_msg = f"ร่าง reply สำหรับข้อความลูกค้านี้:\n\n{content}"
    elif cmd == "EM":
        skill = SKILL_EM
        user_msg = f"ร่าง email reply สำหรับอีเมลนี้:\n\n{content}"
    else:
        return None

    if not skill:
        return f"❌ ไม่พบ skill file สำหรับ tony {cmd}\nกรุณาตรวจสอบ skills/{_skill_filename(cmd)}"

    try:
        messages = [
            {"role": "system", "content": skill},
            {"role": "user", "content": user_msg},
        ]
        reply = await chat_completion(messages)

        # Trim to LINE limit
        if len(reply) > LINE_MAX_CHARS:
            reply = reply[:LINE_MAX_CHARS] + "\n\n[ตัดที่ 4800 ตัวอักษร — ตอบยาวเกิน LINE limit]"

        return reply

    except Exception as e:
        logger.error("Admin command tony %s failed: %s", cmd, e)
        return f"❌ เกิดข้อผิดพลาด ({type(e).__name__})\nลองใหม่อีกครั้งครับ"


def _skill_filename(cmd: str) -> str:
    return {"TR": "แปล.md", "RP": "ตอบลูกค้า.md", "EM": "ตอบอีเมล.md"}.get(cmd, "")
