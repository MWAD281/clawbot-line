import datetime

def log(tag: str, payload: dict):
    ts = datetime.datetime.utcnow().isoformat()
    print(f"{tag} | {ts} | {payload}")
