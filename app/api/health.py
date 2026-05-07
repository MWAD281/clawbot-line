import asyncio
import logging
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

_cache: dict = {"ts": 0.0, "result": None}
_CACHE_TTL = 30.0


@router.get("/health")
async def health_check():
    now = time.monotonic()
    if _cache["result"] and (now - _cache["ts"]) < _CACHE_TTL:
        cached = _cache["result"]
        return JSONResponse(status_code=cached["http_status"], content=cached["body"])

    checks: dict = {}

    try:
        from app.services.openai_service import get_client
        client = get_client()
        await asyncio.wait_for(client.models.list(), timeout=5.0)
        checks["openai"] = "ok"
    except asyncio.TimeoutError:
        checks["openai"] = "timeout"
        logger.warning("Health check: OpenAI timed out")
    except Exception as e:
        checks["openai"] = "error"
        logger.warning("Health check: OpenAI error: %s", type(e).__name__)

    try:
        from app.services.line_service import get_line_client
        client = get_line_client()
        await asyncio.wait_for(client.get_bot_info(), timeout=5.0)
        checks["line"] = "ok"
    except asyncio.TimeoutError:
        checks["line"] = "timeout"
        logger.warning("Health check: LINE timed out")
    except Exception as e:
        checks["line"] = "error"
        logger.warning("Health check: LINE error: %s", type(e).__name__)

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    http_status = 200 if status == "ok" else 503

    body = {"status": status, "checks": checks, "env": get_settings().app_env}
    _cache["result"] = {"http_status": http_status, "body": body}
    _cache["ts"] = now

    return JSONResponse(status_code=http_status, content=body)
