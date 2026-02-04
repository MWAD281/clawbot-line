import json
from datetime import datetime


def log(tag: str, **data):
    payload = {
        "tag": tag,
        "timestamp": datetime.utcnow().isoformat(),
        **data,
    }
    print(json.dumps(payload))
