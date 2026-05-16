#!/usr/bin/env python3
"""
CERAFIELD Quotation PDF Generator
Usage: python3 scripts/generate_quote.py [QT_NUMBER]
       python3 scripts/generate_quote.py         (generates all Pending/Draft quotes)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SPREADSHEET_ID = "184d7kpY7swRCwSJ_eZi8UtrH2K57U1Wzb2Fc9_ShVC8"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
OUTPUT_DIR = Path.home() / "Desktop" / "CERAFIELD" / "Quotations"
FONTS_DIR = Path(__file__).parent / "fonts"

BRAND_NAVY = colors.HexColor("#1C2B5E")
BRAND_GOLD = colors.HexColor("#F5B800")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#CCCCCC")

# Official retail price list (THB)
PRICE_LIST: dict[str, float] = {
    "CF-2495": 8800, "CF-13022": 10800, "CF-2493": 8580, "CF-2507": 8580,
    "CF-12014": 22880, "CF-12016": 23880,
    "CF-15001": 15880, "CF-15005": 10800,
    "CF-4037": 12800, "CF-U622": 15280,
    "CF-600": 1980, "CF-C425": 21800, "CF-B425": 18880,
    "CF-18004": 12800, "CF-2138": 3080, "CF-S01": 850,
}


def _register_fonts() -> tuple[str, str]:
    reg = FONTS_DIR / "Sarabun-Regular.ttf"
    bold = FONTS_DIR / "Sarabun-Bold.ttf"
    if reg.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Sarabun", str(reg)))
        pdfmetrics.registerFont(TTFont("Sarabun-Bold", str(bold)))
        return "Sarabun", "Sarabun-Bold"
    return "Helvetica", "Helvetica-Bold"


def _style(font, font_bold, **kwargs) -> dict:
    return {"fontName": kwargs.pop("bold", False) and font_bold or font, **kwargs}


def get_sheet():
    creds_file = Path.home() / "Downloads" / "cerafield-56ac158f5e16.json"
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    elif creds_file.exists():
        creds = Credentials.from_service_account_file(str(creds_file), scopes=SCOPES)
    else:
        raise RuntimeError("No Google credentials found")
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet("📋 Quotations")


def parse_products(products_str: str) -> list[dict]:
    """Parse 'CF-2495 x10, CF-13022 x5' → list of {sku, qty, unit_price, amount}"""
    items = []
    for part in products_str.split(","):
        part = part.strip()
        if not part:
            continue
        qty = 1
        if " x" in part.lower():
            idx = part.lower().rfind(" x")
            sku = part[:idx].strip().upper()
            try:
                qty = int(part[idx + 2:].strip())
            except ValueError:
                pass
        else:
            sku = part.upper()
        unit_price = PRICE_LIST.get(sku, 0.0)
        items.append({"sku": sku, "qty": qty, "unit_price": unit_price, "amount": unit_price * qty})
    return items


def build_pdf(row: dict, output_path: Path) -> None:
    font, font_bold = _register_fonts()

    qt_no = row.get("Quote No.", "CF-QT-XXXX")
    customer = row.get("Customer / Company", "-")
    project = row.get("Project", "-")
    date_issued = row.get("Date Issued", datetime.now().strftime("%d/%m/%Y"))
    valid_until = row.get("Valid Until", "-")
    products_str = row.get("Products (Summary)", "")
    notes = row.get("Notes", "")

    items = parse_products(products_str)

    # Use subtotal from sheet if provided, else calculate from price list
    subtotal_raw = str(row.get("Subtotal (฿)", "")).replace(",", "").strip()
    if subtotal_raw and float(subtotal_raw) > 0:
        subtotal = float(subtotal_raw)
    else:
        subtotal = sum(i["amount"] for i in items)

    vat = round(subtotal * 0.07, 2)
    total = round(subtotal + vat, 2)

    def P(text, size=9, bold=False, color=colors.black, align="LEFT"):
        return Paragraph(text, ParagraphStyle(
            "p", fontName=font_bold if bold else font,
            fontSize=size, leading=size * 1.4,
            textColor=color, alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}[align],
        ))

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=15*mm, bottomMargin=20*mm,
    )
    w = A4[0] - 40*mm
    story = []

    # Header
    hdr = Table([[
        P("CERAFIELD", size=28, bold=True, color=BRAND_NAVY),
        P(
            "CERAFIELD INTERNATIONAL (THAILAND) CO., LTD.\n"
            "423/48 Moo 1, Makham Khu, Nikhom Pattana, Rayong 21180\n"
            "Tel: +66 956162552  |  supapat.r@cerafield.com\n"
            "www.cerafield.co.th",
            size=8, color=colors.gray,
        ),
    ]], colWidths=[w * 0.42, w * 0.58])
    hdr.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ALIGN", (1,0), (1,0), "RIGHT")]))
    story.append(hdr)
    story.append(HRFlowable(width=w, color=BRAND_GOLD, thickness=2, spaceAfter=6))

    # Quote title + meta
    meta = Table([[
        P("QUOTATION", size=22, bold=True, color=BRAND_NAVY),
        Table([
            [P("Quote No.", bold=True), P(qt_no, bold=True)],
            [P("Date Issued"), P(date_issued)],
            [P("Valid Until"), P(valid_until)],
        ], colWidths=[30*mm, 50*mm], style=TableStyle([
            ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ])),
    ]], colWidths=[w * 0.5, w * 0.5])
    meta.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ALIGN", (1,0), (1,0), "RIGHT")]))
    story.append(meta)
    story.append(Spacer(1, 6*mm))

    # Bill To
    bt_hdr = Table([[P("BILL TO", size=8, bold=True, color=colors.white)]], colWidths=[w])
    bt_hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND_NAVY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(bt_hdr)
    bt_body = Table([
        [P(customer, bold=True, size=10)],
        [P(f"Project: {project}")],
    ], colWidths=[w])
    bt_body.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(bt_body)
    story.append(Spacer(1, 6*mm))

    # Products table
    prod_rows = [[
        P("#", bold=True, color=colors.white, align="CENTER"),
        P("SKU / Description", bold=True, color=colors.white),
        P("Qty", bold=True, color=colors.white, align="CENTER"),
        P("Unit Price (THB)", bold=True, color=colors.white, align="RIGHT"),
        P("Amount (THB)", bold=True, color=colors.white, align="RIGHT"),
    ]]
    for i, item in enumerate(items, 1):
        prod_rows.append([
            P(str(i), align="CENTER"),
            P(item["sku"]),
            P(str(item["qty"]), align="CENTER"),
            P(f"{item['unit_price']:,.2f}", align="RIGHT"),
            P(f"{item['amount']:,.2f}", align="RIGHT"),
        ])

    col_w = [10*mm, w * 0.42, 18*mm, 38*mm, 38*mm]
    pt = Table(prod_rows, colWidths=col_w)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_NAVY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, MID_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 4*mm))

    # Totals
    tt = Table([
        ["", P("Subtotal", align="RIGHT"), P(f"THB {subtotal:,.2f}", align="RIGHT")],
        ["", P("VAT 7%", align="RIGHT"), P(f"THB {vat:,.2f}", align="RIGHT")],
        ["", P("TOTAL", bold=True, size=11, color=colors.white, align="RIGHT"),
              P(f"THB {total:,.2f}", bold=True, size=11, color=colors.white, align="RIGHT")],
    ], colWidths=[w * 0.52, 42*mm, 38*mm])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (1,2), (-1,2), BRAND_NAVY),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEABOVE", (1,2), (-1,2), 1.5, BRAND_GOLD),
    ]))
    story.append(tt)
    story.append(Spacer(1, 8*mm))

    # Notes
    if notes:
        story.append(P("Notes:", bold=True))
        story.append(Spacer(1, 1*mm))
        story.append(P(notes))
        story.append(Spacer(1, 4*mm))

    # Terms
    terms = [
        "1. Quotation valid for 30 days from date issued.",
        "2. Prices are exclusive of VAT 7% unless stated otherwise.",
        "3. Lead time: 4-8 weeks depending on product and stock availability.",
        "4. Payment terms: 50% deposit upon order confirmation, 50% before delivery.",
        "5. Ceramic warranty: 10 years. Fittings & accessories warranty: 1 year.",
    ]
    story.append(P("Terms & Conditions:", bold=True))
    story.append(Spacer(1, 1*mm))
    for t in terms:
        story.append(P(t, size=8, color=colors.gray))
    story.append(Spacer(1, 10*mm))

    # Signature
    sig = Table([[
        Table([
            [P("Authorised by", size=8, color=colors.gray)],
            [Spacer(1, 14*mm)],
            [HRFlowable(width=60*mm, color=MID_GRAY)],
            [P("CERAFIELD INTERNATIONAL (THAILAND)", size=8, color=colors.gray)],
        ], colWidths=[70*mm]),
        Table([
            [P("Accepted by", size=8, color=colors.gray)],
            [Spacer(1, 14*mm)],
            [HRFlowable(width=60*mm, color=MID_GRAY)],
            [P("Customer Signature / Date", size=8, color=colors.gray)],
        ], colWidths=[70*mm]),
    ]], colWidths=[w * 0.5, w * 0.5])
    story.append(sig)
    doc.build(story)


def main():
    ws = get_sheet()
    rows = ws.get_all_records()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target_qt = sys.argv[1] if len(sys.argv) > 1 else None
    generated = []

    for row in rows:
        qt_no = str(row.get("Quote No.", "")).strip()
        status = str(row.get("Status", "")).strip().lower()
        if not qt_no:
            continue
        if target_qt and qt_no != target_qt:
            continue
        if not target_qt and status not in ("pending", "draft", ""):
            continue

        safe_name = qt_no.replace("/", "-").replace(" ", "_")
        customer = str(row.get("Customer / Company", "client")).replace(" ", "_")[:20]
        output_path = OUTPUT_DIR / f"{safe_name}_{customer}.pdf"
        print(f"Generating {output_path.name} ...")
        build_pdf(row, output_path)
        generated.append(str(output_path))

    if generated:
        print(f"\nDone — {len(generated)} PDF(s) saved to ~/Desktop/CERAFIELD/Quotations/")
        for p in generated:
            print(f"  {p}")
    else:
        print("No matching quotations found.")


if __name__ == "__main__":
    main()
