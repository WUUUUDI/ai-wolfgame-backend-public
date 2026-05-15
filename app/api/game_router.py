from fastapi import APIRouter, HTTPException
from starlette import status

from access import CurrentUser
from app.game.manager.room_manager import room_manager
from app.schemas.common import BizResponse

router = APIRouter(prefix="/game", tags=["game"])

@router.post("/create/{room_id}")
async def create_room(room_id: str, current_user: CurrentUser):
    """创建游戏房间"""
    room = room_manager.create_room(room_id)
    return BizResponse.success(
        data={"room_id": room_id}
    )

@router.post("/get_state/{room_id}")
async def get_name_state(room_id: str, current_user: CurrentUser):
    """获取当前房间状态"""
    state = await room_manager.get_current_state(room_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到房间")

    return BizResponse.success(data=state)
