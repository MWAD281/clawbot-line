import json
import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Conversation history store.  Uses Redis when REDIS_URL is set (24h TTL per
    user); falls back to an in-process defaultdict when Redis is unavailable.
    """

    def __init__(self, max_history: int = 10, redis_url: Optional[str] = None):
        self._max_history = max_history
        self._redis_url = redis_url
        self._redis = None
        self._memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

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


_store: Optional[ConversationStore] = None


def get_store() -> ConversationStore:
    global _store
    if _store is None:
        from app.config import get_settings
        s = get_settings()
        _store = ConversationStore(max_history=s.max_history_messages, redis_url=s.redis_url)
    return _store
