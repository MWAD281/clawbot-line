# api.py
from fastapi import FastAPI

from world.market_probe import get_market_snapshot

app = FastAPI(title="ClawBot API")


@app.get("/")
def root():
    return {
        "service": "clawbot-line",
        "status": "alive",
        "phase": 96,
    }


@app.get("/market")
def market():
    return get_market_snapshot()


@app.get("/health")
def health():
    return {"ok": True}
