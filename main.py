# main.py
from fastapi import FastAPI
from api import router as api_router

app = FastAPI(title="ClawBot")

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok"}
