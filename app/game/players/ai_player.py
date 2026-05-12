import random
from typing import Dict, Any

from app.game.players.base import BasePlayer


class AIPlayer(BasePlayer):
    async def get_action(self, state: Dict, action_type: str, context: Any) -> Dict:
        if action_type.lower() == "vote":
            candidates = context.get("candidates", [])
            return random.choice(candidates) if candidates else None
        elif action_type.lower() == "speak":
            return "这是AI随机发言"
        elif action_type.lower() == "night_kill":
            return random.choice(state["alive_ids"])
        # ... 其他行动类型
        return None