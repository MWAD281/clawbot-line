# memory/ceo_memory.py
# 🧠 Phase 12.1 – CEO Memory Compression

import time
import json
import random
from pathlib import Path

# -------------------------
# STORAGE
# -------------------------

BASE_DIR = Path("memory_store")
BASE_DIR.mkdir(exist_ok=True)

MEMORY_FILE = BASE_DIR / "ceo_memory.json"


def _load():
    if not MEMORY_FILE.exists():
        return {}
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def _save(data: dict):
    MEMORY_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# -------------------------
# CORE MEMORY API
# -------------------------

def record_experience(
    ceo_id: str,
    signal: str,
    outcome: str,
    score: float
):
    """
    เก็บประสบการณ์ดิบของ CEO
    """
    data = _load()

    ceo = data.setdefault(ceo_id, {
        "experiences": [],
        "compressed": []
    })

    ceo["experiences"].append({
        "ts": time.time(),
        "signal": signal,
        "outcome": outcome,
        "score": score
    })

    # limit raw memory
    ceo["experiences"] = ceo["experiences"][-100:]

    _save(data)


def compress_memory(ceo_id: str):
    """
    สรุปประสบการณ์ → แก่นความคิด (compressed memory)
    """
    data = _load()
    ceo = data.get(ceo_id)

    if not ceo or not ceo["experiences"]:
        return None

    # simple heuristic compression
    avg_score = sum(e["score"] for e in ceo["experiences"]) / len(ceo["experiences"])

    dominant_outcomes = {}
    for e in ceo["experiences"]:
        dominant_outcomes[e["outcome"]] = dominant_outcomes.get(e["outcome"], 0) + 1

    key_outcome = max(dominant_outcomes, key=dominant_outcomes.get)

    compressed = {
        "ts": time.time(),
        "belief": key_outcome,
        "confidence": round(min(0.95, max(0.1, abs(avg_score))), 2),
        "bias": "risk_off" if avg_score < 0 else "risk_on"
    }

    ceo["compressed"].append(compressed)

    # limit compressed memory
    ceo["compressed"] = ceo["compressed"][-10:]

    _save(data)
    return compressed


def get_compressed_memory(ceo_id: str):
    data = _load()
    return data.get(ceo_id, {}).get("compressed", [])


# -------------------------
# INHERITANCE
# -------------------------

def inherit_memory(parent_ids: list[str]) -> dict:
    """
    CEO ใหม่ inherit แก่นความคิดจาก CEO เก่ง
    """
    data = _load()

    inherited = []
    for pid in parent_ids:
        inherited += data.get(pid, {}).get("compressed", [])

    if not inherited:
        return {}

    sample = random.sample(
        inherited,
        k=min(2, len(inherited))
    )

    return {
        "inherited_beliefs": sample,
        "inherited_bias": max(
            set(m["bias"] for m in sample),
            key=lambda b: [m["bias"] for m in sample].count(b)
        )
    }
