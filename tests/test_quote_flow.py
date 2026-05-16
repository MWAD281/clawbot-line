import pytest
from unittest.mock import AsyncMock, patch

from app.services.quote_flow_service import handle_quote_flow, start_quote_flow


class MockStore:
    def __init__(self, initial_state=None):
        self._state = initial_state

    async def get_quote_flow(self, user_id):
        return self._state

    async def set_quote_flow(self, user_id, state):
        self._state = state

    async def clear_quote_flow(self, user_id):
        self._state = None


@pytest.mark.asyncio
async def test_start_quote_flow_sets_state():
    store = MockStore()
    reply = await start_quote_flow("U123", store)
    assert "ชื่อลูกค้า" in reply
    assert store._state == {"step": "asking_customer"}


@pytest.mark.asyncio
async def test_cancel_clears_flow():
    store = MockStore({"step": "asking_customer"})
    reply = await handle_quote_flow("U123", "ยกเลิก", store)
    assert "ยกเลิก" in reply
    assert store._state is None


@pytest.mark.asyncio
async def test_no_active_flow_returns_none():
    store = MockStore(None)
    result = await handle_quote_flow("U123", "hello", store)
    assert result is None


@pytest.mark.asyncio
async def test_step_asking_customer():
    store = MockStore({"step": "asking_customer"})
    reply = await handle_quote_flow("U123", "Holiday Inn", store)
    assert "โปรเจกต์" in reply
    assert store._state["customer"] == "Holiday Inn"
    assert store._state["step"] == "asking_project"


@pytest.mark.asyncio
async def test_step_asking_project_with_dash():
    store = MockStore({"step": "asking_project", "customer": "Holiday Inn"})
    reply = await handle_quote_flow("U123", "-", store)
    assert store._state["project"] == ""
    assert store._state["step"] == "asking_products"
    assert "CF-" in reply


@pytest.mark.asyncio
async def test_step_asking_project_with_name():
    store = MockStore({"step": "asking_project", "customer": "Sansiri"})
    await handle_quote_flow("U123", "Nue Proud", store)
    assert store._state["project"] == "Nue Proud"


@pytest.mark.asyncio
async def test_step_asking_products_unknown_sku():
    store = MockStore({"step": "asking_products", "customer": "Test", "project": ""})
    reply = await handle_quote_flow("U123", "CF-FAKE x5", store)
    assert "ไม่พบรหัส" in reply
    assert store._state is not None  # state preserved for retry


@pytest.mark.asyncio
async def test_step_asking_products_empty():
    store = MockStore({"step": "asking_products", "customer": "Test", "project": ""})
    reply = await handle_quote_flow("U123", "nothing here", store)
    # "nothing here" parses as unknown SKU → should prompt user to retry
    assert reply is not None
    assert store._state is not None  # state preserved for retry


@pytest.mark.asyncio
async def test_full_flow_creates_quotation():
    store = MockStore({"step": "asking_products", "customer": "Holiday Inn", "project": "ห้อง 201"})
    mock_result = {
        "qt_no": "CF-QT-2026-005",
        "customer": "Holiday Inn",
        "project": "ห้อง 201",
        "items": [{"sku": "CF-13022", "qty": 2, "unit_price": 10800, "amount": 21600}],
        "subtotal": 21600,
        "vat": 1512,
        "total": 23112,
        "drive_url": "https://drive.google.com/file/d/abc/view",
        "drive_error": None,
    }
    with patch("app.services.quote_flow_service.create_quotation", new_callable=AsyncMock, return_value=mock_result):
        reply = await handle_quote_flow("U123", "CF-13022 x2", store)

    assert "CF-QT-2026-005" in reply
    assert "23,112" in reply
    assert "drive.google.com" in reply
    assert store._state is None  # cleared after success
