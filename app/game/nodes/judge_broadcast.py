from tkinter import END
from typing import Literal

from app.game.game_messages import PlayerSpeechMessage
from app.game.state import GameState


async def judge_broadcast(state: GameState) -> dict:
    if state["phase"] == "夜晚":
        content = "天黑请闭眼,狼人请睁眼..."
    elif state["phase"] == "白天":
        content = "天亮了, 所有人睁眼"
    else:
        content = "游戏继续..."

    msg = PlayerSpeechMessage(player_id="1001", role="裁判", content=content)
    return {"speeches": [msg]}

async def router_after_broadcast(state: GameState) -> Literal["process_night_role", "process_speech", "prepare_vote", END]:
    if state["phase"] == "夜晚":
        return "process_night_role"
    elif state["phase"] == "白天":

        return "process_speech"
    elif state["phase"] == "投票":
        return "prepare_vote"
    elif state["phase"] == "结束":
        return END
    else:
        return "prepare_vote"  # 默认

