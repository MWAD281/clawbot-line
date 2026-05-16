import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import _make_completion_response


def _make_lead(**kwargs):
    defaults = {
        "Lead ID": "CF-L-001", "Name": "Test Lead", "Company": "Test Co",
        "Type": "Developer", "Stage": "New", "Priority": "High",
        "Next Action Date": "01/01/2026", "Notes": "",
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.asyncio
async def test_sales_agent_no_user_id(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "")
    from app.config import get_settings
    get_settings.cache_clear()
    from app.agents.sales_agent import run_sales_agent
    await run_sales_agent()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sales_agent_sends_followup(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    lead = _make_lead(**{"Next Action Date": "01/01/2026"})
    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = [lead]

    with (
        patch("app.agents.sales_agent.get_crm_sheet", return_value=mock_ws),
        patch("app.agents.sales_agent.create_completion", new_callable=AsyncMock) as mock_ai,
        patch("app.agents.sales_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        mock_ai.return_value = _make_completion_response("ติดต่อกลับด่วน")
        from app.agents.sales_agent import run_sales_agent
        await run_sales_agent()

    mock_push.assert_called_once()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sales_agent_no_overdue(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    lead = _make_lead(**{"Next Action Date": "31/12/2099"})
    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = [lead]

    with (
        patch("app.agents.sales_agent.get_crm_sheet", return_value=mock_ws),
        patch("app.agents.sales_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        from app.agents.sales_agent import run_sales_agent
        await run_sales_agent()

    mock_push.assert_called_once()
    assert "ไม่มี lead" in mock_push.call_args[0][1]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_intelligence_agent_sends_brief(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    with (
        patch("app.agents.intelligence_agent.create_completion", new_callable=AsyncMock) as mock_ai,
        patch("app.agents.intelligence_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        mock_ai.return_value = _make_completion_response("ตลาดปกติ")
        from app.agents.intelligence_agent import run_intelligence_agent
        await run_intelligence_agent()

    mock_push.assert_called_once()
    assert "Intelligence Agent" in mock_push.call_args[0][1]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ceo_agent_sends_memo(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = [
        _make_lead(Stage="New"), _make_lead(Stage="Qualified"),
    ]

    with (
        patch("app.agents.ceo_agent.get_crm_sheet", return_value=mock_ws),
        patch("app.agents.ceo_agent.create_completion", new_callable=AsyncMock) as mock_ai,
        patch("app.agents.ceo_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        mock_ai.return_value = _make_completion_response("Priority: ปิดดีล Sansiri")
        from app.agents.ceo_agent import run_ceo_agent
        await run_ceo_agent()

    mock_push.assert_called_once()
    assert "CEO Agent" in mock_push.call_args[0][1]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_operations_agent_no_alert_when_stock_ok(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = [
        {"SKU": "CF-2495", "Stock": 50, "Last Updated": "16/05/2026"},
        {"SKU": "CF-13022", "Stock": 30, "Last Updated": "16/05/2026"},
    ]

    with (
        patch("app.agents.operations_agent.get_crm_sheet", return_value=mock_ws),
        patch("app.agents.operations_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        from app.agents.operations_agent import run_operations_agent
        await run_operations_agent()

    mock_push.assert_not_called()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_operations_agent_sends_alert_when_low(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    mock_ws = MagicMock()
    mock_ws.get_all_records.return_value = [
        {"SKU": "CF-2495", "Stock": 3, "Last Updated": "16/05/2026"},
    ]

    with (
        patch("app.agents.operations_agent.get_crm_sheet", return_value=mock_ws),
        patch("app.agents.operations_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        from app.agents.operations_agent import run_operations_agent
        await run_operations_agent()

    mock_push.assert_called_once()
    assert "Stock Alert" in mock_push.call_args[0][1]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_marketing_agent_writes_drafts(monkeypatch):
    monkeypatch.setenv("TONY_LINE_USER_ID", "U123")
    from app.config import get_settings
    get_settings.cache_clear()

    with (
        patch("app.agents.marketing_agent.create_completion", new_callable=AsyncMock) as mock_ai,
        patch("app.agents.marketing_agent.append_to_sheet") as mock_append,
        patch("app.agents.marketing_agent.push_text", new_callable=AsyncMock) as mock_push,
    ):
        mock_ai.return_value = _make_completion_response("โพสต์สินค้า CERAFIELD")
        from app.agents.marketing_agent import run_marketing_agent
        await run_marketing_agent()

    assert mock_append.call_count == 5
    mock_push.assert_called_once()
    assert "drafts" in mock_push.call_args[0][1]
    get_settings.cache_clear()
