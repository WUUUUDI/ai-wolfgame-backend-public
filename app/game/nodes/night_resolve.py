import random
from tkinter import END
from typing import Literal, Counter

from app.game.nodes import judge_broadcast
from app.game.players.ai_player import AIPlayer
from app.game.state import GameState


async def night_resolve(state: GameState) -> dict:
    night_actions = state.get("night_actions", {})
    werewolf_actions = night_actions.get("狼人", {})
    seer_actions = night_actions.get("预言家", {})
    witch_actions = night_actions.get("女巫", {})
    guard_actions = night_actions.get("守卫", {})

    players = state["players"]

    # 1. 狼人击杀
    kill_target = None
    if werewolf_actions:
        targets = list(werewolf_actions.values())
        counter = Counter(targets)
        max_count = max(counter.values())
        top_targets = [tid for tid, cnt in counter.items() if cnt == max_count]
        kill_target = top_targets[0] if len(top_targets) == 1 else None

    killed = set()
    if kill_target and kill_target in state["alive_ids"]:
        killed.add(kill_target)
        for p in players:
            if p["id"] == kill_target:
                p["is_alive"] = False
                break

    # 2. 女巫解药与毒药
    antidote_target = None
    poison_target = None
    if witch_actions:
        witch_action = next(iter(witch_actions.values()))
        use_antidote = witch_action.get("use_antidote", False)
        use_poison = witch_action.get("use_poison", False)
        target_id = witch_action.get("target_id")
        # 解药救人
        if use_antidote and target_id in killed:
            killed.remove(target_id)
            antidote_target = target_id
            state["witch_has_antidote"] = False
        # 毒药
        if use_poison and target_id and target_id in state["alive_ids"]:
            killed.add(target_id)
            poison_target = target_id
            state["witch_has_poison"] = False

    # 3. 守卫守护
    if guard_actions:
        guard_target = next(iter(guard_actions.values()))
        if guard_target and guard_target in killed:
            # 同守同救：如果女巫解药也救了同一人，则此人死亡（即不能救活）
            if antidote_target == guard_target:
                killed.add(guard_target)   # 确保在 killed 中
            else:
                killed.discard(guard_target)

    # 4. 预言家查验
    seer_checks = state.get("seer_checks", {})
    for seer_id, target_id in seer_actions.items():
        target_player = next((p for p in players if p["id"] == target_id), None)
        if target_player:
            real_role = target_player["role"]
            if seer_id not in seer_checks:
                seer_checks[seer_id] = {}
            seer_checks[seer_id][target_id] = real_role

    # 5. 猎人开枪
    hunter_has_shot = state.get("hunter_has_shot", False)
    if not hunter_has_shot:
        # 找出死亡的猎人
        dead_hunter = None
        for dead_id in killed:
            dead_player = next((p for p in players if p["id"] == dead_id), None)
            if dead_player and dead_player["role"] == "猎人":
                dead_hunter = dead_player
                break
        if dead_hunter:
            ai = AIPlayer(dead_hunter["id"])
            candidates = [pid for pid in state["alive_ids"] if pid != dead_hunter["id"]]
            if candidates:
                random.shuffle(candidates)
                context = {"candidates": candidates}
                shot_target_id = await ai.get_action(state, "hunter_shot_action", context)
                if shot_target_id and shot_target_id in state["alive_ids"]:
                    killed.add(shot_target_id)
                    for p in players:
                        if p["id"] == shot_target_id:
                            p["is_alive"] = False
                            break
                    hunter_has_shot = True

    # 6. 更新存活列表
    new_alive = [pid for pid in state["alive_ids"] if pid not in killed]
    for p in players:
        if p["id"] in killed:
            p["is_alive"] = False

    # 白天发言顺序
    if new_alive:
        player_seat_map = {p["id"]: p["seat"] for p in players}
        wait_to_speak_queue = sorted(new_alive, key=lambda pid: player_seat_map[pid])
    else:
        wait_to_speak_queue = []

    return {
        "killed_tonight": killed,
        "alive_ids": new_alive,
        "phase": "白天",
        "night_actions": {},
        "current_night_role_idx": 0,
        "wait_to_speak_queue": wait_to_speak_queue,
        "players": players,
        "hunter_has_shot": hunter_has_shot,
        "seer_checks": seer_checks,
        "witch_has_antidote": state.get("witch_has_antidote", True),
        "witch_has_poison": state.get("witch_has_poison", True),
        "pending_wolf_kill": None
    }

async def after_night(state: GameState) -> Literal["check_winner", END]:
    game_over = state["game_over"]

    if not game_over:
        return "check_winner"
    else:
        return END