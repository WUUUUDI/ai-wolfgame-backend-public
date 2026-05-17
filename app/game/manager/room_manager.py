import uuid
from typing import Dict, Optional

from langgraph.checkpoint.memory import MemorySaver

from app.game.graph import build_game_graph, get_initial_state
from app.game.state import GameState


class RoomManager:

    def __init__(self):
        self.rooms = {}
        self.checkpointer = MemorySaver()

    def room_exists(self, room_id: str) -> bool:
        return room_id in self.rooms

    def create_room(self, players_config: list=None) -> dict:
        """生成唯一 room_id 创建房间, 返回房间信息"""

        while True:
            room_id = str(uuid.uuid4())[:8]  # 取前8位作为短ID，也可用完整UUID
            if room_id not in self.rooms:
                break

        graph = build_game_graph(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": room_id}}
        initial_state = get_initial_state()
        initial_state["room_id"] = room_id

        if players_config:
            initial_state["players_config"] = players_config

        room = {
            "room_id": room_id,
            "graph": graph,
            "config": config,
            "state": initial_state,
            "task": None, # 占位（后台任务）
            "websocket": None # 存储当前房间的ws连接
        }

        self.rooms[room_id] = room

        return room

    async def get_current_state(self, room_id: str) -> Optional[GameState]:
        """从 checkpoint 中获取最新的状态"""
        room = self.rooms.get(room_id)
        if not room:
            return None
        # 使用 aget_state 读取最新状态（包含所有历史）
        state = await room["graph"].aget_state(room["config"])
        return state.values if state else None

    def get_room(self, room_id: str):
        return self.rooms.get(room_id)

room_manager = RoomManager()




