from collections import defaultdict, deque
from typing import List, Dict


class ConversationStore:
    def __init__(self, max_history: int = 10):
        self._store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

    def add_message(self, user_id: str, role: str, content: str) -> None:
        self._store[user_id].append({"role": role, "content": content})

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return list(self._store[user_id])

    def clear(self, user_id: str) -> None:
        self._store[user_id].clear()


conversation_store = ConversationStore()
