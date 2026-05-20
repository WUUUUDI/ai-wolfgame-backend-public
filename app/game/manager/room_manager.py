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

    def create_room(self, players_config: list = None) -> dict:
        """生成唯一 room_id 创建房间, 返回房间信息"""
        # 校验玩家人数
        if players_config is not None:
            num_players = len(players_config)
            if num_players not in [6, 9, 12]:
                raise ValueError(f"Unsupported number of players: {num_players}. Only 6, 9, 12 are allowed.")

        while True:
            room_id = str(uuid.uuid4())[:8]
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
            "task": None,
            "websocket": None
        }

        self.rooms[room_id] = room

        return room

    async def get_current_state(self, room_id: str) -> Optional[GameState]:
        room = self.rooms.get(room_id)
        if not room:
            return None
        state = await room["graph"].aget_state(room["config"])
        return state.values if state else None

    def get_room(self, room_id: str):
        return self.rooms.get(room_id)

room_manager = RoomManager()