from typing import TypedDict


class PlayerSpeechMessage(TypedDict):
    player_id: str # 发言玩家 id
    content: str # 发言内容
    role: str