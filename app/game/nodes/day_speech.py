from typing import Dict, Literal
from app.game.state import GameState
from app.game.players.ai_player import AIPlayer
from app.game.GameMessages import PlayerSpeechMessage

async def process_speech(state: GameState) -> Dict:
    """
    处理当前发言玩家（队列头），返回新消息和更新后的队列。
    """
    queue = state["wait_to_speak_queue"]
    if not queue:
        return {}

    current_player_id = queue[0]
    # 查找玩家信息
    player = next((p for p in state["players"] if p["id"] == current_player_id), None)
    if not player:
        # 玩家不在列表中（异常），跳过
        return {"wait_to_speak_queue": queue[1:]}

    # 获取发言内容
    if player["is_human"]:
        # TODO: 使用 interrupt 等待真实玩家输入
        # 占位处理：返回固定文本
        content = "人类玩家发言（待实现中断）"
    else:
        ai = AIPlayer()
        # 传递空 context 或相关上下文
        content = await ai.get_action(state, "speak", {})

    # 创建自定义消息
    msg = PlayerSpeechMessage(
        role=player["role"],
        player_id=current_player_id,
        content=content
    )

    return {
        "wait_to_speak_queue": queue[1:],   # 移除当前玩家
        "speeches": [msg]                   # 自动追加
    }

async def should_continue_speech(state: GameState) -> Literal["process_speech", "prepare_vote"]:
    if state["wait_to_speak_queue"]:
        return "process_speech"
    else:
        return "prepare_vote"