import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Clawbot LINE bot starting up")
    yield
    logger.info("Clawbot LINE bot shutting down")


app = FastAPI(title="Clawbot LINE Bot", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(webhook_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {"status": "clawbot-alive"}
