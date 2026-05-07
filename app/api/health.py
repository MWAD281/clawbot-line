import logging

from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    checks: dict = {}

    try:
        from app.services.openai_service import get_client
        get_client()
        checks["openai"] = "configured"
    except Exception as e:
        checks["openai"] = f"error: {e}"

    try:
        from app.services.line_service import get_line_client
        get_line_client()
        checks["line"] = "configured"
    except Exception as e:
        checks["line"] = f"error: {e}"

    status = "ok" if all("error" not in str(v) for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "env": settings.app_env}
