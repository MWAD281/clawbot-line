# world/ceos/base.py

from memory.ceo_memory import recall, remember


class BaseCEO:
    id = "base"
    faction = "NEUTRAL"
    personality = {}

    def think(self, text: str, world_state: dict):
        raise NotImplementedError

    def vote(self, text: str, world_state: dict):
        memory = recall(self.id)

        result = self.think(text, world_state)

        remember(self.id, {
            "text": text,
            "result": result
        })

        return {
            "agent_id": self.id,
            "faction": self.faction,
            **result
        }
