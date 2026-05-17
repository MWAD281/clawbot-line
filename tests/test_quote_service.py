import pytest
from unittest.mock import MagicMock, patch

from app.services.quote_service import parse_quote_command


def test_parse_quote_command_basic():
    result = parse_quote_command("/quote Holiday Inn, CF-13022 x10, CF-600 x5")
    assert result["customer"] == "Holiday Inn"
    assert result["project"] == ""
    assert len(result["items"]) == 2
    assert result["items"][0]["sku"] == "CF-13022"
    assert result["items"][0]["qty"] == 10
    assert result["items"][0]["unit_price"] == 10800
    assert result["items"][0]["amount"] == 108000
    assert result["items"][1]["sku"] == "CF-600"
    assert result["items"][1]["qty"] == 5
    assert result["items"][1]["amount"] == 9900


def test_parse_quote_command_with_project():
    result = parse_quote_command("/quote Sansiri / Nue Proud, CF-2493 x20")
    assert result["customer"] == "Sansiri"
    assert result["project"] == "Nue Proud"
    assert result["items"][0]["sku"] == "CF-2493"
    assert result["items"][0]["qty"] == 20


def test_parse_quote_command_unknown_sku():
    result = parse_quote_command("/quote Test Co, CF-UNKNOWN x3")
    assert result["items"][0]["unit_price"] == 0.0
    assert result["items"][0]["amount"] == 0.0


def test_parse_quote_command_no_qty():
    result = parse_quote_command("/quote Test Co, CF-2495")
    assert result["items"][0]["qty"] == 1
    assert result["items"][0]["amount"] == 8580


def test_parse_quote_command_empty():
    result = parse_quote_command("/quote")
    assert result == {} or not result.get("items")


@pytest.mark.asyncio
async def test_create_quotation_returns_dict():
    mock_ws = MagicMock()
    mock_ws.col_values.return_value = ["CF-QT-2026-001"]

    with (
        patch("app.services.quote_service.get_crm_sheet", return_value=mock_ws),
        patch("app.services.quote_service.append_to_sheet"),
        patch("app.services.quote_service.upload_to_drive", return_value=("https://drive.google.com/test", None)),
    ):
        from app.services.quote_service import create_quotation
        items = [{"sku": "CF-13022", "qty": 2, "unit_price": 10800, "amount": 21600}]
        result = await create_quotation("Test Customer", "Test Project", items)

    assert result["customer"] == "Test Customer"
    assert result["subtotal"] == 21600
    assert result["vat"] == pytest.approx(21600 * 0.07, abs=1)
    assert result["total"] == pytest.approx(21600 * 1.07, abs=1)
    assert result["drive_url"] == "https://drive.google.com/test"
