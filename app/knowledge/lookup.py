import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent / "products.json"

_CATEGORY_TH = {
    "one_piece": "โถสุขภัณฑ์แบบชิ้นเดียว (One Piece)",
    "two_piece": "โถสุขภัณฑ์แบบสองชิ้น (Two Piece)",
    "wall_hung": "โถสุขภัณฑ์แบบแขวนผนัง (Wall Hung)",
    "floor_standing": "โถสุขภัณฑ์แบบตั้งพื้น",
    "smart_toilet": "โถสุขภัณฑ์อัจฉริยะ",
    "urinal": "โถปัสสาวะชาย",
    "basin_wall": "อ่างล้างหน้าแบบแขวนผนัง",
    "basin_countertop": "อ่างล้างหน้าแบบวางบนเคาน์เตอร์",
    "basin_pedestal": "อ่างล้างหน้าแบบตั้งพื้น",
    "basin_half_pedestal": "อ่างล้างหน้าพร้อมขาครึ่งตัว",
    "concealed_cistern": "ถังเก็บน้ำแบบซ่อน (Concealed Cistern)",
    "safety_handrail": "ราวจับนิรภัย",
    "shower_seat": "เก้าอี้อาบน้ำ",
    "bidet_spray": "สายฉีดชำระ",
    "seat_cover": "ฝารองนั่ง",
    "faucet": "ก๊อกน้ำ",
}


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def get_product(sku: str) -> Optional[dict]:
    return _load().get(sku.upper())


def find_skus_in_text(text: str) -> list[str]:
    """Return all CF-XXXXX codes found in text (uppercase)."""
    return [m.upper() for m in re.findall(r"CF-[A-Z0-9]+", text, re.IGNORECASE)]


def _format_product(sku: str, p: dict) -> str:
    lines = [f"{sku} — {p.get('name_th', '')}"]
    if p.get("series"):
        lines.append(f"ซีรีส์: {p['series']}")
    if p.get("flush"):
        lines.append(f"ระบบชำระล้าง: {p['flush']}")
    if p.get("dimensions"):
        lines.append(f"ขนาด: {p['dimensions']}")
    if p.get("drain"):
        lines.append(f"ท่อน้ำทิ้ง: {p['drain']}")
    if p.get("seat"):
        lines.append(f"ฝารองนั่ง: {p['seat']}")
    if p.get("fitting"):
        lines.append(f"อุปกรณ์ติดตั้ง: {p['fitting']}")
    if p.get("material"):
        lines.append(f"วัสดุ: {p['material']}")
    if p.get("system"):
        lines.append(f"ระบบ: {p['system']}")
    if p.get("weight_capacity"):
        lines.append(f"รับน้ำหนัก: {p['weight_capacity']}")
    if p.get("includes"):
        lines.append(f"อุปกรณ์ในชุด: {', '.join(p['includes'])}")
    if p.get("notes"):
        lines.append(f"หมายเหตุ: {p['notes']}")

    colors = p.get("colors")
    if isinstance(colors, dict):
        color_info = []
        for c, v in colors.items():
            if isinstance(v, dict):
                price = v.get("list_price")
                moq = v.get("moq")
                if price:
                    entry = f"{c}: {price:,} บาท"
                    if moq:
                        entry += f" (MOQ {moq} ชิ้น)"
                    color_info.append(entry)
        if color_info:
            lines.append("ราคาตามสี: " + " / ".join(color_info))
    elif isinstance(colors, list):
        lines.append(f"สีที่มี: {', '.join(colors)}")

    lp = p.get("list_price")
    if lp and not isinstance(p.get("colors"), dict):
        lines.append(f"ราคา: {lp:,} บาท")
    pp = p.get("project_price")
    if pp:
        lines.append(f"ราคาโปรเจค {pp['min_qty']}+ ชิ้น: {pp['price']:,} บาท/ชิ้น")

    return "\n".join(lines)


def build_spec_context(text: str) -> str:
    """
    Scan text for CF- codes, return formatted spec block if any found.
    Returns empty string if no matching SKUs.
    """
    skus = find_skus_in_text(text)
    if not skus:
        return ""
    db = _load()
    blocks = []
    seen = set()
    for sku in skus:
        if sku in seen or sku not in db:
            continue
        seen.add(sku)
        blocks.append(_format_product(sku, db[sku]))
    if not blocks:
        return ""
    return "--- ข้อมูลสินค้า ---\n" + "\n\n".join(blocks) + "\n---"
