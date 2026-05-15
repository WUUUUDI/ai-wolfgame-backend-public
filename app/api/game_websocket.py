from typing import Dict

from fastapi import WebSocket, WebSocketDisconnect, Query
from app.game.manager.room_manager import room_manager
from app.utils.security import decode_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, room_id:str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[room_id] = websocket

    def disconnect(self, room_id:str):
        self.active_connections.pop(room_id, None)

    async def send_message(self, room_id:str, message:dict):
        """发送消息给room_id房间号的所有活跃的websocket连接"""
        if room_id in self.active_connections:
            try:
                await self.active_connections[room_id].send_json(message)
            except:
                pass

manager = ConnectionManager()

async def game_websocket(websocket: WebSocket, room_id:str, token:str = Query(...)):
    # 验证 token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    # 接受连接
    await manager.connect(room_id, websocket)
    # todo 中断处理
    try:
        # 确保房间存在
        room = room_manager.create_room(room_id)
        config = room["config"]
        graph = room["graph"]

        # 获取当前状态
        current_state = await graph.aget_state(config)
        # 如果状态中有 __interrupt__，说明游戏正在等待用户输入
        if current_state.tasks and current_state.tasks[0].interrupts:
            interrupts = current_state.tasks[0].interrupts
            await manager.send_message(room_id, {"type": "interrupt", "data": interrupts[0].value})

        # 接收前端消息
        while True:
            data = await websocket.receive_json()
            cmd = data.get("cmd")

            if cmd == "start":
                # 开始新游戏
                async for chunk in graph.astream(room["state"], config, stream_mode="updates"):
                    await manager.send_message(room_id, chunk)
                    # 检查是否遇到中断
                    state_after = await graph.aget_state(config)
                    if state_after.tasks and state_after.tasks[0].interrupts:
                        # 发送中断信息，等待前端决策
                        interrupts = state_after.tasks[0].interrupts
                        await manager.send_message(room_id, {"type": "interrupt", "data": interrupts[0].value})
                        break
                # 更新保存的状态
                room["state"] = (await graph.aget_state(config)).values

            elif cmd == "decision":
                # 恢复中断，提交决策
                resume_value = data.get("resume")
                if resume_value is None:
                    await manager.send_message(room_id, {"type": "error", "message": "Missing resume value"})
                    continue
                # 发送 Command(resume=...)
                async for chunk in graph.astream(Command(resume=resume_value), config, stream_mode="updates"):
                    await manager.send_message(room_id, chunk)
                    state_after = await graph.aget_state(config)
                    if state_after.tasks and state_after.tasks[0].interrupts:
                        interrupts = state_after.tasks[0].interrupts
                        await manager.send_message(room_id, {"type": "interrupt", "data": interrupts[0].value})
                        break
                room["state"] = (await graph.aget_state(config)).values

            elif cmd == "get_state":
                state = await room_manager.get_current_state(room_id)
                await manager.send_message(room_id, {"type": "state", "data": state})

            else:
                await manager.send_message(room_id, {"type": "error", "message": f"Unknown command: {cmd}"})
    except WebSocketDisconnect:
        manager.disconnect(room_id)