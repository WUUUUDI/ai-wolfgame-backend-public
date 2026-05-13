from typing import Literal

from pip._internal.models import candidate

from app.game.players.ai_player import AIPlayer
from app.game.state import GameState


async def cast_vote(state: GameState) -> dict:
    """处理当前投票队列的第一个玩家"""
    queue = state["wait_to_vote_queue"]
    if not queue:
        return {}

    voter_id = queue[0]
    player = next(p for p in state["players"] if p["id"] == voter_id)
    candidates = [pid for pid in state["alive_ids"] if pid!= voter_id]

    if not candidates:
        # 无人可投，弃权
        return {"wait_to_vote_queue": queue[1:], "give_up_vote_queue": [voter_id]}

    if player["is_human"]:
        # todo interrupt
        pass
    else:
        ai = AIPlayer(player["id"])
        target = await ai.get_action(state, "vote", {"candidates": candidates})

    return {
        "votes": {voter_id: target},
        "wait_to_vote_queue": queue[1:]
    }

async def should_continue_vote(state: GameState) -> Literal["cast_vote", "vote_resolve"]:
    if state["wait_to_vote_queue"]:
        return "cast_vote"
    else:
        return "vote_resolve"