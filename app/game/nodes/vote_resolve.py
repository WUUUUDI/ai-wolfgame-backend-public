from typing import Counter

from app.game.state import GameState


async def vote_resolve(state: GameState) -> dict:
    """统计投票，放逐最高票玩家"""
    players = state["players"]
    votes = state.get("votes", {})
    if not votes:
        return {"phase": "夜晚", "voted_out": ""}
    counter = Counter(votes.values())
    if not counter:
        return {"phase": "夜晚", "voted_out": ""}
    max_votes = max(counter.values())
    most_voted = [pid for pid, cnt in counter.items() if cnt == max_votes]
    eliminated = most_voted[0] if len(most_voted) == 1 else None  # 平票无人出局
    new_alive = state["alive_ids"]
    if eliminated and eliminated in new_alive:
        for p in players:
            if p["id"] == eliminated:
                p["is_alive"] = False
                break
        new_alive.remove(eliminated)
    return {
        "voted_out": eliminated or "",
        "alive_ids": new_alive,
        "phase": "夜晚",
        # 重置投票相关状态
        "votes": {},
        "wait_to_vote_queue": [],
        "give_up_vote_queue": [],
        "night_actions": {},
        "current_night_role_idx": 0,
        # 重置夜晚死亡集合
        "killed_tonight": set(),
    }