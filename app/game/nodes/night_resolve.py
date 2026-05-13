import random
from tkinter import END
from typing import Literal, Counter

from app.game.nodes import judge_broadcast
from app.game.state import GameState


async def night_resolve(state:GameState) -> dict:
    """结算夜晚死亡：从 night_actions 中提取狼人击杀的目标，确定死者"""
    night_actions = state.get("night_actions", {})
    werewolf_actions = night_actions.get("狼人", {})
    seer_actions = night_actions.get("预言家", {})

    players = state["players"]

    # 获取所有狼人目标的多数
    kill_target = None
    if werewolf_actions:
        # 取最多投票的目标
        kill_target = None
        targets = list(werewolf_actions.values())
        counter = Counter(targets)
        max_count = max(counter.values())
        top_targets = [tid for tid, cnt in counter.items() if cnt == max_count]
        # 平票不杀
        kill_target = top_targets[0] if len(top_targets) == 1 else None
    killed = set()

    if kill_target and kill_target in state["alive_ids"]:
        killed.add(kill_target)
        for p in players:
            if p["id"] == kill_target:
                p["is_alive"] = False
                break

    # 预言家查验结算
    seer_checks = state.get("seer_checks", {})
    for seer_id, target_id in seer_checks.items():
        target_player = next((p for p in players if p["id"] == target_id), None)
        if target_player:
            real_role = target_player["role"]
            # 记录到 seer_checks
            if seer_id not in seer_checks:
                seer_checks[seer_id] = {}
            seer_checks[seer_id][target_player["id"]] = real_role


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
        "seer_actions": seer_actions,
        "current_night_role_idx": 0,
        # 准备白天发言队列（存活玩家随机顺序）
        "wait_to_speak_queue": wait_to_speak_queue
    }

async def after_night(state: GameState) -> Literal["check_winner", END]:
    game_over = state["game_over"]

    if not game_over:
        return "check_winner"
    else:
        return END