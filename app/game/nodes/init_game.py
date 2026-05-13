import random

from app.game.state import GameState


async def init_game(state: GameState) -> dict:
    """根据玩家配置初始化游戏：分配角色、发言顺序、夜晚行动顺序等"""
    players = state["players"]
    if not players:
        # 测试使用：6个玩家
        players = [
            {"id": f"{i}", "name": f"玩家{i}", "role": "村民", "is_alive": True, "is_human": False, "seat": i, "difficulty": "中等", "strategy": "理性逻辑"} for i in range(1, 7)
        ]
        # 简单随机分配角色
        roles = ["狼人", "狼人", "预言家"] + ["村民"] * 3
        random.shuffle(roles)

        for p, r in zip(players, roles):
            p["role"] = r

    alive_ids = [p["id"] for p in players if p["is_alive"]]
    night_role_order = []

    # 生成角色夜晚行动顺序（暂定狼人、预言家）
    if any(p["role"] == "狼人" for p in players):
        night_role_order.append("狼人")
    elif any(p["role"] == "预言家" for p in players):
        night_role_order.append("预言家")

    speak_queue = random.sample(alive_ids, len(alive_ids))

    return {
        "players": players,
        "alive_ids": alive_ids,
        "night_role_order": night_role_order,
        "current_night_role_idx": 0,
        "night_actions": {},
        "wait_to_speak_queue": speak_queue,
        "phase": "夜晚",
        "game_over": False,
        "winner": None,
        "speeches": [],
        "wait_to_vote_queue": [],
        "votes": {},
        "give_up_vote_queue": [],
        "killed_tonight": set(),
        "voted_out": "",
    }

