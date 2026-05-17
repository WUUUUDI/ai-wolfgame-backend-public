# app/api/game_websocket.py
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect, Query
from langgraph.types import Command   # 注意：原代码写成了 langchain_protocol，应该是 langgraph

from app.game.manager.room_manager import room_manager
from app.utils.security import decode_token
from app.game.game_event_formatter import (
    format_game_event,
    format_interrupt,
    format_error,
    format_state
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[room_id] = websocket

    def disconnect(self, room_id: str):
        self.active_connections.pop(room_id, None)

    async def send_message(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            try:
                await self.active_connections[room_id].send_json(message)
            except:
                pass

manager = ConnectionManager()

async def game_websocket(websocket: WebSocket, room_id: str, token: str = Query(...)):
    # 验证 token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    await manager.connect(room_id, websocket)

    try:
        room = room_manager.get_room(room_id)
        if not room:
            await manager.send_message(room_id, format_error("Room not found", room_id))
        config = room["config"]
        graph = room["graph"]

        # 获取当前状态
        current_state = await graph.aget_state(config)
        if current_state.tasks and current_state.tasks[0].interrupts:
            interrupts = current_state.tasks[0].interrupts
            await manager.send_message(room_id, format_interrupt(interrupts[0].value, room_id))

        while True:
            data = await websocket.receive_json()
            cmd = data.get("cmd")

            if cmd == "start":
                async for chunk in graph.astream(room["state"], config, stream_mode="updates"):
                    # chunk 格式: {"node_name": {...}}
                    for event_name, event_data in chunk.items():
                        # 获取当前阶段
                        state_after = await graph.aget_state(config)
                        phase = state_after.values.get("phase") if state_after.values else None
                        wrapped = format_game_event(event_name, event_data, phase, room_id)
                        print(wrapped)
                        await manager.send_message(room_id, wrapped)

                        if state_after.tasks and state_after.tasks[0].interrupts:
                            interrupts = state_after.tasks[0].interrupts
                            await manager.send_message(room_id, format_interrupt(interrupts[0].value, room_id))
                            break
                    else:
                        continue
                    break  # 遇到中断则退出循环
                room["state"] = (await graph.aget_state(config)).values

            elif cmd == "decision":
                resume_value = data.get("resume")
                if resume_value is None:
                    await manager.send_message(room_id, format_error("Missing resume value", room_id))
                    continue
                async for chunk in graph.astream(Command(resume=resume_value), config, stream_mode="updates"):
                    for event_name, event_data in chunk.items():
                        state_after = await graph.aget_state(config)
                        phase = state_after.values.get("phase") if state_after.values else None
                        wrapped = format_game_event(event_name, event_data, phase, room_id)
                        await manager.send_message(room_id, wrapped)

                        if state_after.tasks and state_after.tasks[0].interrupts:
                            interrupts = state_after.tasks[0].interrupts
                            await manager.send_message(room_id, format_interrupt(interrupts[0].value, room_id))
                            break
                    else:
                        continue
                    break
                room["state"] = (await graph.aget_state(config)).values

            elif cmd == "get_state":
                state = await room_manager.get_current_state(room_id)
                await manager.send_message(room_id, format_state(state, room_id))

            else:
                await manager.send_message(room_id, format_error(f"Unknown command: {cmd}", room_id))

    except WebSocketDisconnect:
        manager.disconnect(room_id)