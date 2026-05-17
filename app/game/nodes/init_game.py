import random

from app.game.state import GameState, Player


async def init_game(state: GameState) -> dict:
    """根据玩家配置初始化游戏：分配角色、发言顺序、夜晚行动顺序等"""
    players_config = state.get("players_config")

    if players_config:
        total = len(players_config)
        roles_pool = []
        # 狼人数 = 总人数 // 3 或者2
        werewolf_count = max(2, total // 3)
        roles_pool.extend(["狼人"] * werewolf_count)
        roles_pool.append("预言家")
        roles_pool.extend(["村民"] * (total - werewolf_count - 1))
        random.shuffle(roles_pool)

        # 根据配置构建Player对象
        players = []
        for idx, cfg in enumerate(players_config):
            player_id = str(idx + 1)
            player_name = str("玩家" + player_id)
            player = Player(
                id = player_id,
                name = player_name,
                role = roles_pool[idx],
                is_alive = True,
                is_human = cfg.get("is_human", False),
                seat = idx,
                difficulty = cfg.get("difficulty", "中等"),
                strategy = cfg.get("strategy", "理性逻辑"),
            )
            players.append(player)
    else:
        # 默认生成6个AI玩家
        players = []
        roles = ["狼人", "狼人", "预言家"] + ["村民"] * 3
        random.shuffle(roles)
        for i in range(1, 7):
            players.append(Player(
                id=str(i),
                name=f"玩家{i}",
                role=roles[i - 1],
                is_alive=True,
                is_human=False,
                seat=i,
                difficulty="中等",
                strategy="理性逻辑",
            ))

    alive_ids = [p["id"] for p in players if p["is_alive"]]
    night_role_order = []

    # 生成角色夜晚行动顺序（暂定狼人、预言家）
    if any(p["role"] == "狼人" for p in players):
        night_role_order.append("狼人")
    if any(p["role"] == "预言家" for p in players):
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

