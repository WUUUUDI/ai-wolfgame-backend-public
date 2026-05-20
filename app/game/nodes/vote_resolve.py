from typing import Counter
from app.game.state import GameState
from app.game.players.ai_player import AIPlayer
import random

async def vote_resolve(state: GameState) -> dict:
    """统计投票，放逐最高票玩家，并处理猎人开枪"""
    players = state["players"]
    votes = state.get("votes", {})
    if not votes:
        return {"phase": "夜晚", "voted_out": ""}
    counter = Counter(votes.values())
    if not counter:
        return {"phase": "夜晚", "voted_out": ""}
    max_votes = max(counter.values())
    most_voted = [pid for pid, cnt in counter.items() if cnt == max_votes]
    eliminated = most_voted[0] if len(most_voted) == 1 else None

    new_alive = state["alive_ids"][:]  # 复制
    killed = set()

    # 1. 放逐玩家
    if eliminated and eliminated in new_alive:
        killed.add(eliminated)
        for p in players:
            if p["id"] == eliminated:
                p["is_alive"] = False
                break
        new_alive.remove(eliminated)

    # 2. 处理猎人开枪（如果被放逐的玩家是猎人且尚未开枪）
    hunter_has_shot = state.get("hunter_has_shot", False)
    hunter_shot_target = None
    if eliminated and not hunter_has_shot:
        dead_player = next((p for p in players if p["id"] == eliminated), None)
        if dead_player and dead_player["role"] == "猎人":
            ai = AIPlayer(dead_player["id"])
            candidates = [pid for pid in new_alive if pid != dead_player["id"]]
            if candidates:
                # 随机打乱，让 AI 选择或保底随机
                random.shuffle(candidates)
                context = {"candidates": candidates}
                try:
                    shot_target_id = await ai.get_action(state, "hunter_shot_action", context)
                except Exception as e:
                    print(f"猎人开枪 AI 调用失败: {e}")
                    shot_target_id = None
                # 如果 AI 返回的目标无效，则随机选择（保底开枪）
                if not shot_target_id or shot_target_id not in new_alive:
                    shot_target_id = random.choice(candidates)
                if shot_target_id:
                    hunter_shot_target = shot_target_id
                    killed.add(hunter_shot_target)
                    for p in players:
                        if p["id"] == hunter_shot_target:
                            p["is_alive"] = False
                            break
                    if hunter_shot_target in new_alive:
                        new_alive.remove(hunter_shot_target)
                    hunter_has_shot = True

    # 3. 最终同步玩家状态
    for p in players:
        if p["id"] in killed:
            p["is_alive"] = False

    return {
        "voted_out": eliminated or "",
        "alive_ids": new_alive,
        "phase": "夜晚",
        "votes": {},
        "wait_to_vote_queue": [],
        "give_up_vote_queue": [],
        "night_actions": {},
        "current_night_role_idx": 0,
        "killed_tonight": set(),
        "hunter_has_shot": hunter_has_shot,
        "players": players,
    }