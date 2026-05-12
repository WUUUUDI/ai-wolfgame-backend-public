import random
from tkinter import END
from typing import Literal

from app.game.nodes import judge_broadcast
from app.game.state import GameState


async def night_resolve(state:GameState) -> dict:
    """结算夜晚死亡：从 night_actions 中提取狼人击杀的目标，确定死者"""
    night_actions = state.get("night_actions", {})
    werewolf_actions = night_actions.get("狼人", {})

    players = state["players"]

    # 获取所有狼人目标的多数
    kill_target = None
    if werewolf_actions:
        # todo 取最多投票的目标，这里只取第一个
        kill_target = list(werewolf_actions.values())[0]
    killed = set()

    if kill_target and kill_target in state["alive_ids"]:
        killed.add(kill_target)
        for p in players:
            if p["id"] == kill_target:
                p["is_alive"] = False
                break

    # todo 加入女巫毒药逻辑



    new_alive = [pid for pid in state["alive_ids"] if pid not in killed]

    # 白天发言顺序（seat从小到大）
    if new_alive:
        # 构建玩家id -> seat 的映射
        player_seat_map = {p["id"]: p["seat"] for p in state["players"]}
        # 按 seat 升序排序
        wait_to_speak_queue = sorted(new_alive, key=lambda pid: player_seat_map[pid])
    else:
        wait_to_speak_queue = []

    return {
        "killed_tonight": killed,
        "alive_ids": new_alive,
        "phase": "白天",
        # 重置夜晚相关状态
        "night_actions": {},
        "current_night_role_idx": 0,
        # 准备白天发言队列（存活玩家随机顺序）
        "wait_to_speak_queue": wait_to_speak_queue
    }

async def after_night(state: GameState) -> Literal["judge_broadcast", END]:
    game_over = state["game_over"]

    if not game_over:
        return "judge_broadcast"
    else:
        return END