import io
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.services.sheets_service import get_crm_sheet, append_to_sheet

logger = logging.getLogger(__name__)

SPREADSHEET_ID = "184d7kpY7swRCwSJ_eZi8UtrH2K57U1Wzb2Fc9_ShVC8"
FONTS_DIR = Path(__file__).parent.parent.parent / "scripts" / "fonts"
OWNER_EMAIL = "tony.cerafield@gmail.com"

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

BRAND_NAVY = colors.HexColor("#1C2B5E")
BRAND_GOLD = colors.HexColor("#F5B800")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#CCCCCC")

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
        try:
            pdfmetrics.registerFont(TTFont("Sarabun", str(reg)))
            pdfmetrics.registerFont(TTFont("Sarabun-Bold", str(bold)))
            return "Sarabun", "Sarabun-Bold"
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold"


def parse_quote_command(text: str) -> dict:
    """
    Parse: /quote Customer Name [/ Project], SKU x Qty, SKU x Qty
    Returns: {customer, project, items: [{sku, qty, unit_price, amount}]}
    """
    body = text[len("/quote"):].strip()
    parts = [p.strip() for p in body.split(",")]
    if not parts:
        return {}

    # First part = customer [/ project]
    first = parts[0]
    if "/" in first:
        customer, project = [x.strip() for x in first.split("/", 1)]
    else:
        customer = first
        project = ""

    items = []
    for part in parts[1:]:
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

    return {"customer": customer, "project": project, "items": items}


def next_qt_number() -> str:
    ws = get_crm_sheet("📋 Quotations")
    year = datetime.now().year
    if ws is None:
        return f"CF-QT-{year}-001"
    ids = ws.col_values(1)[1:]  # skip header
    prefix = f"CF-QT-{year}-"
    nums = []
    for i in ids:
        if i.startswith(prefix):
            try:
                nums.append(int(i[len(prefix):]))
            except ValueError:
                pass
    n = max(nums) + 1 if nums else 1
    return f"{prefix}{n:03d}"


def build_pdf_bytes(qt_no, customer, project, items, subtotal, notes="") -> bytes:
    font, font_bold = _register_fonts()
    vat = round(subtotal * 0.07, 2)
    total = round(subtotal + vat, 2)
    today = datetime.now()
    valid = today + timedelta(days=30)

    def P(text, size=9, bold=False, color=colors.black, align="LEFT"):
        return Paragraph(str(text), ParagraphStyle(
            "p", fontName=font_bold if bold else font,
            fontSize=size, leading=size * 1.4, textColor=color,
            alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}[align],
        ))

    buf = io.BytesIO()
    w = A4[0] - 40 * mm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=15*mm, bottomMargin=20*mm)
    story = []

    # Header
    hdr = Table([[
        P("CERAFIELD", size=28, bold=True, color=BRAND_NAVY),
        P("CERAFIELD INTERNATIONAL (THAILAND) CO., LTD.\n"
          "423/48 Moo 1, Makham Khu, Nikhom Pattana, Rayong 21180\n"
          "Tel: +66 956162552  |  supapat.r@cerafield.com\n"
          "www.cerafield.co.th", size=8, color=colors.gray),
    ]], colWidths=[w * 0.42, w * 0.58])
    hdr.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(hdr)
    story.append(HRFlowable(width=w, color=BRAND_GOLD, thickness=2, spaceAfter=6))

    meta = Table([[
        P("QUOTATION", size=22, bold=True, color=BRAND_NAVY),
        Table([
            [P("Quote No.", bold=True), P(qt_no, bold=True)],
            [P("Date Issued"), P(today.strftime("%d/%m/%Y"))],
            [P("Valid Until"), P(valid.strftime("%d/%m/%Y"))],
        ], colWidths=[30*mm, 50*mm], style=TableStyle([
            ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ])),
    ]], colWidths=[w * 0.5, w * 0.5])
    meta.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(meta)
    story.append(Spacer(1, 6*mm))

    bt_hdr = Table([[P("BILL TO", size=8, bold=True, color=colors.white)]], colWidths=[w])
    bt_hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND_NAVY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(bt_hdr)
    bt_body = Table([
        [P(customer, bold=True, size=10)],
        [P(f"Project: {project}" if project else "")],
    ], colWidths=[w])
    bt_body.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(bt_body)
    story.append(Spacer(1, 6*mm))

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

    pt = Table(prod_rows, colWidths=[10*mm, w*0.42, 18*mm, 38*mm, 38*mm])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_NAVY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, MID_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 4*mm))

    tt = Table([
        ["", P("Subtotal", align="RIGHT"), P(f"THB {subtotal:,.2f}", align="RIGHT")],
        ["", P("VAT 7%", align="RIGHT"), P(f"THB {vat:,.2f}", align="RIGHT")],
        ["", P("TOTAL", bold=True, size=11, color=colors.white, align="RIGHT"),
              P(f"THB {total:,.2f}", bold=True, size=11, color=colors.white, align="RIGHT")],
    ], colWidths=[w*0.52, 42*mm, 38*mm])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (1,2), (-1,2), BRAND_NAVY),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LINEABOVE", (1,2), (-1,2), 1.5, BRAND_GOLD),
    ]))
    story.append(tt)
    story.append(Spacer(1, 8*mm))

    if notes:
        story.append(P("Notes:", bold=True))
        story.append(Spacer(1, 1*mm))
        story.append(P(notes))
        story.append(Spacer(1, 4*mm))

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

    sig = Table([[
        Table([[P("Authorised by", size=8, color=colors.gray)], [Spacer(1, 14*mm)],
               [HRFlowable(width=60*mm, color=MID_GRAY)],
               [P("CERAFIELD INTERNATIONAL (THAILAND)", size=8, color=colors.gray)]],
              colWidths=[70*mm]),
        Table([[P("Accepted by", size=8, color=colors.gray)], [Spacer(1, 14*mm)],
               [HRFlowable(width=60*mm, color=MID_GRAY)],
               [P("Customer Signature / Date", size=8, color=colors.gray)]],
              colWidths=[70*mm]),
    ]], colWidths=[w*0.5, w*0.5])
    story.append(sig)

    doc.build(story)
    return buf.getvalue()


def _drive_creds() -> Optional[Credentials]:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        return None
    try:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=DRIVE_SCOPES)
        creds.refresh(Request())
        return creds
    except Exception as e:
        logger.error("Drive creds error: %s", e)
        return None


def upload_to_drive(pdf_bytes: bytes, filename: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (url, error_msg). url is None on failure; error_msg describes the problem."""
    creds = _drive_creds()
    if creds is None:
        return None, "Drive creds failed (GOOGLE_CREDENTIALS_JSON missing or invalid)"
    try:
        from app.config import get_settings
        folder_id = get_settings().drive_folder_id
        headers = {"Authorization": f"Bearer {creds.token}"}
        boundary = "cerafield_qt_boundary"
        meta: dict = {"name": filename}
        if folder_id:
            meta["parents"] = [folder_id]
        metadata = json.dumps(meta)
        body = (
            f"--{boundary}\r\nContent-Type: application/json\r\n\r\n{metadata}\r\n"
            f"--{boundary}\r\nContent-Type: application/pdf\r\n\r\n"
        ).encode() + pdf_bytes + f"\r\n--{boundary}--".encode()

        resp = httpx.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
            headers={**headers, "Content-Type": f"multipart/related; boundary={boundary}"},
            content=body, timeout=30,
        )
        if not resp.is_success:
            msg = f"Drive upload HTTP {resp.status_code}: {resp.text[:200]}"
            logger.error(msg)
            return None, msg
        file_id = resp.json()["id"]

        # Share with Tony
        share_resp = httpx.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            headers=headers,
            json={"role": "reader", "type": "user", "emailAddress": OWNER_EMAIL,
                  "sendNotificationEmail": False},
            timeout=10,
        )
        if not share_resp.is_success:
            logger.warning("Drive share failed HTTP %s: %s", share_resp.status_code, share_resp.text[:200])
        return f"https://drive.google.com/file/d/{file_id}/view", None
    except Exception as e:
        msg = f"Drive upload exception: {type(e).__name__}: {e}"
        logger.error(msg)
        return None, msg


async def create_quotation(customer: str, project: str, items: list, notes: str = "") -> dict:
    """Full flow: QT number → Sheets → PDF → Drive. Returns result dict."""
    qt_no = next_qt_number()
    today = datetime.now()
    valid = today + timedelta(days=30)
    subtotal = sum(i["amount"] for i in items)
    vat = round(subtotal * 0.07, 2)
    total = round(subtotal + vat, 2)
    products_summary = ", ".join(f"{i['sku']} x{i['qty']}" for i in items)

    # Save to Sheets
    append_to_sheet("📋 Quotations", [
        qt_no,
        today.strftime("%d/%m/%Y"),
        valid.strftime("%d/%m/%Y"),
        customer,
        project,
        products_summary,
        subtotal,
        vat,
        total,
        "Pending",
        "Tony",
        "", "",
        notes,
    ])

    # Generate PDF
    pdf_bytes = build_pdf_bytes(qt_no, customer, project, items, subtotal, notes)

    # Upload to Drive
    filename = f"{qt_no}_{customer[:20].replace(' ', '_')}.pdf"
    drive_url, drive_error = upload_to_drive(pdf_bytes, filename)

    return {
        "qt_no": qt_no,
        "customer": customer,
        "project": project,
        "items": items,
        "subtotal": subtotal,
        "vat": vat,
        "total": total,
        "drive_url": drive_url,
        "drive_error": drive_error,
    }
