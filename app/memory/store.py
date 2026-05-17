import datetime
import json
import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Conversation history and usage store.  Uses Redis when REDIS_URL is set (24h TTL
    per user); falls back to an in-process defaultdict when Redis is unavailable.
    """

    def __init__(self, max_history: int = 10, redis_url: Optional[str] = None):
        self._max_history = max_history
        self._redis_url = redis_url
        self._redis = None
        self._memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._usage: Dict[str, int] = {}
        self._quote_flows: Dict[str, dict] = {}
        self._lead_flows: Dict[str, dict] = {}

    async def _get_redis(self):
        if not self._redis_url:
            return None
        if self._redis is None:
            try:
                import redis.asyncio as aioredis  # optional dependency
                self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
                await self._redis.ping()
                logger.info("Redis conversation store connected")
            except Exception as e:
                logger.warning("Redis unavailable, using in-memory store: %s", type(e).__name__)
                self._redis_url = None
                self._redis = None
        return self._redis

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        r = await self._get_redis()
        if r:
            key = f"conv:{user_id}"
            try:
                raw = await r.get(key)
                messages = json.loads(raw) if raw else []
                messages.append({"role": role, "content": content})
                messages = messages[-self._max_history:]
                await r.set(key, json.dumps(messages), ex=86400)
                return
            except Exception as e:
                logger.warning("Redis write error, falling back to memory: %s", type(e).__name__)
        self._memory[user_id].append({"role": role, "content": content})

    async def get_history(self, user_id: str) -> List[Dict[str, str]]:
        r = await self._get_redis()
        if r:
            key = f"conv:{user_id}"
            try:
                raw = await r.get(key)
                return json.loads(raw) if raw else []
            except Exception as e:
                logger.warning("Redis read error, falling back to memory: %s", type(e).__name__)
        return list(self._memory[user_id])

    async def clear(self, user_id: str) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.delete(f"conv:{user_id}")
                return
            except Exception as e:
                logger.warning("Redis delete error: %s", type(e).__name__)
        self._memory[user_id].clear()

    async def get_daily_usage(self, user_id: str) -> int:
        today = datetime.date.today().isoformat()
        r = await self._get_redis()
        if r:
            key = f"usage:{today}:{user_id}"
            try:
                val = await r.get(key)
                return int(val) if val else 0
            except Exception as e:
                logger.warning("Redis usage read error: %s", type(e).__name__)
        return self._usage.get(f"{today}:{user_id}", 0)

    async def get_quote_flow(self, user_id: str) -> Optional[dict]:
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(f"qflow:{user_id}")
                return json.loads(raw) if raw else None
            except Exception:
                pass
        return self._quote_flows.get(user_id)

    async def set_quote_flow(self, user_id: str, state: dict) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.set(f"qflow:{user_id}", json.dumps(state), ex=1800)
                return
            except Exception:
                pass
        self._quote_flows[user_id] = state

    async def get_lead_flow(self, user_id: str) -> Optional[dict]:
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(f"lflow:{user_id}")
                return json.loads(raw) if raw else None
            except Exception:
                pass
        return self._lead_flows.get(user_id)

    async def set_lead_flow(self, user_id: str, state: dict) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.set(f"lflow:{user_id}", json.dumps(state), ex=1800)
                return
            except Exception:
                pass
        self._lead_flows[user_id] = state

    async def clear_lead_flow(self, user_id: str) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.delete(f"lflow:{user_id}")
                return
            except Exception:
                pass
        self._lead_flows.pop(user_id, None)

    async def clear_quote_flow(self, user_id: str) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.delete(f"qflow:{user_id}")
                return
            except Exception:
                pass
        self._quote_flows.pop(user_id, None)

    async def increment_daily_usage(self, user_id: str) -> int:
        today = datetime.date.today().isoformat()
        r = await self._get_redis()
        if r:
            key = f"usage:{today}:{user_id}"
            try:
                count = await r.incr(key)
                if count == 1:
                    await r.expire(key, 90000)  # 25h so it safely spans a midnight rollover
                return count
            except Exception as e:
                logger.warning("Redis usage write error: %s", type(e).__name__)
        mem_key = f"{today}:{user_id}"
        self._usage[mem_key] = self._usage.get(mem_key, 0) + 1
        return self._usage[mem_key]


_store: Optional[ConversationStore] = None


def get_store() -> ConversationStore:
    global _store
    if _store is None:
        from app.config import get_settings
        s = get_settings()
        _store = ConversationStore(max_history=s.max_history_messages, redis_url=s.redis_url)
    return _store
