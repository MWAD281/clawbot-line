from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "clawbot-alive"}


@app.get("/health")
def health():
    return {"health": "ok"}
