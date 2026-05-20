import random

from app.game.state import GameState, Player


def assign_roles(players_count: int) -> list:
    """
        根据玩家数量分配角色（狼人:神职:平民 = 1:1:1）
        支持人数: 6, 9, 12
        神职角色池: 预言家、女巫、守卫、猎人 (按顺序取)
        """
    if players_count not in [6, 9, 12]:
        raise ValueError(f"Unsupported player count: {players_count}. Only 6, 9, 12 are allowed.")

    faction_size = players_count // 3
    werewolves = ["狼人"] * faction_size

    # 神职角色列表
    all_roles = ["预言家", "女巫", "守卫", "猎人"]
    # 取前 faction_size 个作为本局神职
    special_roles = all_roles[:faction_size]
    # 如果神职数量不足，补齐村民（正常应该相等，这里留作安全）
    while len(special_roles) < faction_size:
        special_roles.append("村民")
    # 平民数量 = faction_size
    villagers = ["村民"] * faction_size

    roles = werewolves + special_roles + villagers
    random.shuffle(roles)
    return roles

async def init_game(state: GameState) -> dict:
    """根据玩家配置初始化游戏：分配角色、发言顺序、夜晚行动顺序等"""
    players_config = state.get("players_config")
    roles = []

    if players_config:
        total = len(players_config)
        roles = assign_roles(total)

        # 根据配置构建Player对象
        players = []
        for idx, cfg in enumerate(players_config):
            player_id = str(idx + 1)
            player_name = str("玩家" + player_id)
            player = Player(
                id = player_id,
                name = player_name,
                role = roles[idx],
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

    # 生成角色夜晚行动顺序
    if any(p["role"] == "狼人" for p in players):
        night_role_order.append("狼人")
    if any(p["role"] == "女巫" for p in players):
        night_role_order.append("女巫")
    if any(p["role"] == "预言家" for p in players):
        night_role_order.append("预言家")
    if any(p["role"] == "守卫" for p in players):
        night_role_order.append("守卫")

    speak_queue = random.sample(alive_ids, len(alive_ids))
    available_roles = list(set(p["role"] for p in players))

    return {
        "players": players,
        "alive_ids": alive_ids,
        "available_roles": available_roles,
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
        "witch_has_antidote": True,
        "witch_has_poison": True,
        "pending_wolf_kill": None,
        "guard_protected_target": None,
        "last_guard_target": None,
        "hunter_has_shot": False
    }

