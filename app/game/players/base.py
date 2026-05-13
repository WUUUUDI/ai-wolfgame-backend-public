from abc import ABC, abstractmethod
from typing import Dict, Any

from app.game.state import RoleType


class BasePlayer(ABC):
    id: str  # 玩家唯一标识

    @abstractmethod
    async def get_action(self, state: Dict, action_type: str, context: Any = None) -> Dict:
        """根据当前状态和行为类型返回决策（投票目标、发言内容）"""
        pass

