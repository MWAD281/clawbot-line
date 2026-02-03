# main.py

from fastapi import FastAPI
from routers.health import router as health_router

app = FastAPI(title="ClawBot")

# Routers
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "service": "clawbot-line",
        "status": "running"
    }
