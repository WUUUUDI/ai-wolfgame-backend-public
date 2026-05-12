from typing import Dict, Any, Literal

from app.game.players.ai_player import AIPlayer
from app.game.state import GameState


async def process_night_role(state: GameState) -> Dict[str, Any]:
    """
    处理当前夜间角色行动（一次处理一个角色类型，由条件边循环调用
    :param state:
    :return:
    """

    role_idx = state['current_night_role_idx']
    if role_idx >= len(state['night_role_order']):
        # 没有更多夜间角色了
        return {}

    # 获取到行动的角色类型
    role = state['night_role_order'][role_idx]
    # 获取该角色类型的存活玩家
    players_of_role = [p for p in state['players'] if p['role'] == role and p['is_alive']]
    actions = {}

    for player in players_of_role:
        if player['is_human']:
            pass
        else:
            ai = AIPlayer()
            if role == "狼人":
                context = {"candidates": [pid for pid in state["players"] if pid != player["id"]]}
                action = await ai.get_action(state, "night_kill", context)
            elif role == "预言家":
                context = {"candidates": state["alive_ids"]}
                action = await ai.get_action(state, "seer_check", context)
            else:
                action = None
        if action is not None:
            actions[player["id"]] = action

    # Todo 为了简单，暂时返回全部
    return {
        "night_actions": {role: actions},
        "current_night_role_idx": role_idx + 1  # 递增索引
    }

async def should_continue_night(state: GameState) -> Literal["process_night_role", "night_resolve"]:
    """条件边，判断是否继续处理下一个夜晚角色，还是进入结算"""
    if state['current_night_role_idx'] < len(state['night_role_order']):
        return "process_night_role"
    else:
        return "night_resolve"