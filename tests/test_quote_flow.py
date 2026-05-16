import pytest
from unittest.mock import AsyncMock, patch

from app.services.quote_flow_service import FlowReply, handle_quote_flow, start_quote_flow


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
async def test_start_flow_returns_quick_reply():
    store = MockStore()
    reply = await start_quote_flow("U123", store)
    assert isinstance(reply, FlowReply)
    assert reply.quick_reply is not None
    assert any("ส่วนตัว" in o for o in reply.quick_reply)
    assert store._state == {"step": "type_select"}


@pytest.mark.asyncio
async def test_cancel_clears_flow():
    store = MockStore({"step": "retail_name", "quote_type": "retail"})
    reply = await handle_quote_flow("U123", "ยกเลิก", store)
    assert "ยกเลิก" in reply.text
    assert store._state is None


@pytest.mark.asyncio
async def test_no_active_flow_returns_none():
    store = MockStore(None)
    result = await handle_quote_flow("U123", "hello", store)
    assert result is None


@pytest.mark.asyncio
async def test_type_select_retail():
    store = MockStore({"step": "type_select"})
    reply = await handle_quote_flow("U123", "ซื้อใช้ส่วนตัว", store)
    assert "ชื่อ" in reply.text
    assert store._state["step"] == "retail_name"
    assert store._state["quote_type"] == "retail"


@pytest.mark.asyncio
async def test_type_select_project():
    store = MockStore({"step": "type_select"})
    reply = await handle_quote_flow("U123", "งานโปรเจค / ธุรกิจ", store)
    assert "บริษัท" in reply.text
    assert store._state["step"] == "project_company"
    assert store._state["quote_type"] == "project"


@pytest.mark.asyncio
async def test_type_select_invalid():
    store = MockStore({"step": "type_select"})
    reply = await handle_quote_flow("U123", "ไม่รู้จะเลือกอะไร", store)
    assert reply.quick_reply is not None
    assert store._state["step"] == "type_select"  # unchanged


@pytest.mark.asyncio
async def test_retail_name_step():
    store = MockStore({"step": "retail_name", "quote_type": "retail", "project": "", "tax_id": ""})
    reply = await handle_quote_flow("U123", "Tony", store)
    assert store._state["customer"] == "Tony"
    assert store._state["step"] == "retail_products"
    assert "CF-" in reply.text


@pytest.mark.asyncio
async def test_retail_products_unknown_sku():
    store = MockStore({"step": "retail_products", "quote_type": "retail",
                       "customer": "Tony", "project": "", "tax_id": ""})
    reply = await handle_quote_flow("U123", "CF-FAKE x5", store)
    assert "ไม่พบรหัส" in reply.text
    assert store._state["step"] == "retail_products"  # not advanced


@pytest.mark.asyncio
async def test_retail_products_valid_shows_confirm():
    store = MockStore({"step": "retail_products", "quote_type": "retail",
                       "customer": "Tony", "project": "", "tax_id": ""})
    reply = await handle_quote_flow("U123", "CF-13022 x2", store)
    assert "สรุป" in reply.text
    assert store._state["step"] == "retail_confirm"
    assert reply.quick_reply == ["ยืนยัน", "แก้ไขสินค้า"]


@pytest.mark.asyncio
async def test_retail_confirm_edit_goes_back():
    store = MockStore({"step": "retail_confirm", "quote_type": "retail",
                       "customer": "Tony", "project": "", "tax_id": "",
                       "items": [{"sku": "CF-13022", "qty": 2, "unit_price": 10800, "amount": 21600}]})
    reply = await handle_quote_flow("U123", "แก้ไขสินค้า", store)
    assert store._state["step"] == "retail_products"
    assert "CF-" in reply.text


@pytest.mark.asyncio
async def test_retail_confirm_generates_pdf():
    items = [{"sku": "CF-13022", "qty": 2, "unit_price": 10800, "amount": 21600}]
    store = MockStore({"step": "retail_confirm", "quote_type": "retail",
                       "customer": "Tony", "project": "", "tax_id": "", "items": items})
    mock_result = {
        "qt_no": "CF-QT-2026-010", "customer": "Tony", "project": "",
        "items": items, "subtotal": 21600, "vat": 1512, "total": 23112,
        "drive_url": "https://drive.google.com/abc", "drive_error": None,
    }
    with patch("app.services.quote_flow_service.create_quotation",
               new_callable=AsyncMock, return_value=mock_result):
        reply = await handle_quote_flow("U123", "ยืนยัน", store)

    assert "CF-QT-2026-010" in reply.text
    assert store._state is None


@pytest.mark.asyncio
async def test_project_company_with_tax_id():
    store = MockStore({"step": "project_company", "quote_type": "project"})
    await handle_quote_flow("U123", "บริษัท ABC จำกัด / 1234567890123", store)
    assert store._state["customer"] == "บริษัท ABC จำกัด"
    assert store._state["tax_id"] == "1234567890123"
    assert store._state["step"] == "project_name"


@pytest.mark.asyncio
async def test_project_company_no_tax_id():
    store = MockStore({"step": "project_company", "quote_type": "project"})
    await handle_quote_flow("U123", "Sansiri", store)
    assert store._state["customer"] == "Sansiri"
    assert store._state["tax_id"] == ""


@pytest.mark.asyncio
async def test_project_products_uses_project_pricing():
    store = MockStore({"step": "project_products", "quote_type": "project",
                       "customer": "Sansiri", "project": "Nue Proud", "tax_id": ""})
    reply = await handle_quote_flow("U123", "CF-13022 x100", store)
    # 100 pcs CF-13022 → project price 5,880
    assert "5,880" in reply.text
    assert store._state["step"] == "project_confirm"
