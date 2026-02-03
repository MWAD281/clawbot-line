from fastapi import APIRouter
from world.market_probe import get_market_snapshot

router = APIRouter()

@router.get("/")
def root():
    return {
        "service": "clawbot-line",
        "phase": 96,
        "market": get_market_snapshot()
    }
