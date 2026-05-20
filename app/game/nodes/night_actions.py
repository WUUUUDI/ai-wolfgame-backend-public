import random
from typing import Dict, Any, Literal, Counter

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
    # 当前相同角色已做出的行动（用于团队协作）
    current_team_actions = {}

    for player in players_of_role:
        if player['is_human']:
            pass
        else:
            ai = AIPlayer(player["id"])
            if role == "狼人":
                # todo 后续狼人可以在夜晚沟通决策
                candidates = [pid for pid in state["alive_ids"] if pid != player["id"]]
                random.shuffle(candidates)
                context = {
                    "candidates": candidates,
                    "team_vote": current_team_actions # 队友已选目标
                }
                action = await ai.get_action(state, "night_kill", context)

                if action:
                    current_team_actions[player["id"]] = action
            elif role == "预言家":
                candidates = [pid for pid in state["alive_ids"] if pid != player["id"]]
                random.shuffle(candidates)
                context = {"candidates": candidates}
                action = await ai.get_action(state, "seer_check", context)
            elif role == "女巫":
                candidates = [pid for pid in state["alive_ids"] if pid != player["id"]]
                random.shuffle(candidates)
                context = {
                    "candidates": candidates,
                    "witch_has_antidote": state["witch_has_antidote"],
                    "witch_has_poison": state["witch_has_poison"],
                    "wolf_target": state["pending_wolf_kill"]
                }
                action = await ai.get_action(state, "witch_action", context)
            elif role == "守卫":
                candidates = state["alive_ids"]
                random.shuffle(candidates)
                context = {
                    "candidates": candidates,
                    "last_guard_target": state.get("last_guard_target")
                }
                action = await ai.get_action(state, "guard_action", context)
            else:
                action = None
        if action is not None:
            actions[player["id"]] = action

    current_night_actions = state.get("night_actions", {})
    # 合并新actions
    merged_actions = {**current_night_actions, role: actions}

    # 如果是狼人，存下临时目标
    pending_wolf_kill = None
    if role == "狼人" and actions:
        targets = list(actions.values())
        counter = Counter(targets)
        max_count = max(counter.values())
        top_targets = [tid for tid, cnt in counter.items() if cnt == max_count]
        pending = top_targets[0] if len(top_targets) == 1 else None
        pending_wolf_kill = pending

    return {
        "night_actions": merged_actions,
        "current_night_role_idx": role_idx + 1,  # 递增索引
        "pending_wolf_kill": pending_wolf_kill
    }

async def should_continue_night(state: GameState) -> Literal["process_night_role", "night_resolve"]:
    """条件边，判断是否继续处理下一个夜晚角色，还是进入结算"""
    if state['current_night_role_idx'] < len(state['night_role_order']):
        return "process_night_role"
    else:
        return "night_resolve"