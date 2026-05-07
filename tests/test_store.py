import datetime
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_add_and_get_history():
    from app.memory.store import ConversationStore

    store = ConversationStore(max_history=5)
    await store.add_message("u1", "user", "Hello")
    await store.add_message("u1", "assistant", "Hi")
    history = await store.get_history("u1")

    assert history == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]


@pytest.mark.asyncio
async def test_max_history_enforced():
    from app.memory.store import ConversationStore

    store = ConversationStore(max_history=2)
    for i in range(5):
        await store.add_message("u1", "user", f"msg{i}")
    history = await store.get_history("u1")

    assert len(history) == 2
    assert history[-1]["content"] == "msg4"


@pytest.mark.asyncio
async def test_clear():
    from app.memory.store import ConversationStore

    store = ConversationStore()
    await store.add_message("u1", "user", "Hello")
    await store.clear("u1")
    assert await store.get_history("u1") == []


@pytest.mark.asyncio
async def test_redis_add_get_and_clear():
    from app.memory.store import ConversationStore

    stored: dict = {}

    async def fake_get(key):
        return stored.get(key)

    async def fake_set(key, value, ex=None):
        stored[key] = value

    async def fake_delete(key):
        stored.pop(key, None)

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=fake_get)
    mock_redis.set = AsyncMock(side_effect=fake_set)
    mock_redis.delete = AsyncMock(side_effect=fake_delete)

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        store = ConversationStore(max_history=5, redis_url="redis://localhost")

        await store.add_message("u1", "user", "Hello")
        history = await store.get_history("u1")
        assert history == [{"role": "user", "content": "Hello"}]

        await store.clear("u1")
        assert await store.get_history("u1") == []


@pytest.mark.asyncio
async def test_redis_connection_failure_falls_back_to_memory():
    from app.memory.store import ConversationStore

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("refused"))

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        store = ConversationStore(redis_url="redis://localhost")
        await store.add_message("u1", "user", "Hello")
        history = await store.get_history("u1")

    assert history == [{"role": "user", "content": "Hello"}]


@pytest.mark.asyncio
async def test_daily_usage_in_memory():
    from app.memory.store import ConversationStore

    store = ConversationStore()

    assert await store.get_daily_usage("u1") == 0
    count = await store.increment_daily_usage("u1")
    assert count == 1
    count = await store.increment_daily_usage("u1")
    assert count == 2
    assert await store.get_daily_usage("u1") == 2


@pytest.mark.asyncio
async def test_daily_usage_different_users_independent():
    from app.memory.store import ConversationStore

    store = ConversationStore()
    await store.increment_daily_usage("ua")
    await store.increment_daily_usage("ua")
    await store.increment_daily_usage("ub")

    assert await store.get_daily_usage("ua") == 2
    assert await store.get_daily_usage("ub") == 1


@pytest.mark.asyncio
async def test_daily_usage_redis():
    from app.memory.store import ConversationStore

    today = datetime.date.today().isoformat()
    stored: dict = {}
    expiry: dict = {}

    async def fake_get(key):
        return stored.get(key)

    async def fake_incr(key):
        stored[key] = str(int(stored.get(key) or "0") + 1)
        return int(stored[key])

    async def fake_expire(key, secs):
        expiry[key] = secs

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=fake_get)
    mock_redis.incr = AsyncMock(side_effect=fake_incr)
    mock_redis.expire = AsyncMock(side_effect=fake_expire)

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        store = ConversationStore(redis_url="redis://localhost")

        assert await store.get_daily_usage("u1") == 0
        count = await store.increment_daily_usage("u1")
        assert count == 1

        key = f"usage:{today}:u1"
        assert expiry.get(key) == 90000

        count = await store.increment_daily_usage("u1")
        assert count == 2
        # expire only called on first increment (count == 1)
        assert mock_redis.expire.call_count == 1
