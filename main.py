import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pythonjsonlogger.json import JsonFormatter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.limiter import limiter
from app.config import get_settings


def _configure_logging() -> None:
    # In test environments keep plain text so pytest output is readable
    if os.getenv("APP_ENV", "production") == "test":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


def _init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    _log = logging.getLogger(__name__)
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
        )
        _log.info("Sentry initialized")
    except ImportError:
        _log.warning(
            "SENTRY_DSN is set but sentry-sdk is not installed; "
            "run: pip install 'sentry-sdk[fastapi]'"
        )


_configure_logging()
_init_sentry()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Clawbot LINE bot starting up")
    settings = get_settings()
    scheduler = None
    if settings.agents_enabled and settings.app_env != "test":
        from app.agents.scheduler import build_scheduler
        scheduler = build_scheduler()
        scheduler.start()
        logger.info("Agent scheduler started (%d jobs)", len(scheduler.get_jobs()))
    yield
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Clawbot LINE bot shutting down")


app = FastAPI(title="Clawbot LINE Bot", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(webhook_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {"status": "clawbot-alive"}
