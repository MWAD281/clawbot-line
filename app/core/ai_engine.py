import logging

from app.memory.store import get_store
from app.services.openai_service import chat_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are Clawbot, a helpful AI assistant. Be concise and friendly."
FALLBACK_MESSAGE = "Sorry, I'm having trouble responding right now. Please try again."


async def get_ai_reply(user_id: str, user_message: str) -> str:
    store = get_store()
    try:
        await store.add_message(user_id, "user", user_message)
        history = await store.get_history(user_id)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        reply = await chat_completion(messages)

        await store.add_message(user_id, "assistant", reply)
        return reply
    except Exception as e:
        logger.error("AI engine error for user %s...: %s", user_id[:8], type(e).__name__)
        return FALLBACK_MESSAGE
