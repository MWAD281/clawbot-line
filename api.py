from fastapi import FastAPI
from routers.health import router as health_router

# import ให้ตรงตำแหน่งจริง
from world.ceos.market_probe import get_market_snapshot

app = FastAPI(title="ClawBot")

app.include_router(health_router)

@app.get("/")
def root():
    return {
        "service": "clawbot-line",
        "phase": 96,
        "market": get_market_snapshot()
    }
