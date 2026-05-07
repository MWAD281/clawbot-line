import logging

from app.memory.store import conversation_store
from app.services.openai_service import chat_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are Clawbot, a helpful AI assistant. Be concise and friendly."

FALLBACK_MESSAGE = "Sorry, I'm having trouble responding right now. Please try again."


async def get_ai_reply(user_id: str, user_message: str) -> str:
    try:
        conversation_store.add_message(user_id, "user", user_message)
        history = conversation_store.get_history(user_id)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        reply = await chat_completion(messages)

        conversation_store.add_message(user_id, "assistant", reply)
        return reply
    except Exception as e:
        logger.error(f"AI engine error for user {user_id}: {e}")
        return FALLBACK_MESSAGE
