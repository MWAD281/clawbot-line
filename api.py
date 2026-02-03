from fastapi import FastAPI

# ✅ import ให้ตรงตำแหน่งจริง
from world.market_probe import get_market_snapshot

app = FastAPI(title="ClawBot")

@app.get("/")
def root():
    return {
        "service": "clawbot-line",
        "status": "ok",
        "market": get_market_snapshot()
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
