from app.game.state import GameState


async def check_winner(state: GameState) -> dict:
    """根据存活玩家判断胜利阵营"""

    alive_ids = state["alive_ids"]
    if not alive_ids:
        return {"winner": "平局", "game_over": True}

    players = state["players"]
    alive_players = [p for p in players if p["id"] in alive_ids]
    werewolves = [p for p in alive_players if p["role"] == "狼人"]
    villagers = [p for p in alive_players if p["role"] != "狼人"]

    winner = None
    game_over = False

    # 狼人数量 >= 好人数量 → 狼人胜利
    if len(werewolves) >= len(villagers):
        winner = "狼人"
        game_over = True
    # 没有狼人 → 好人胜利
    if len(werewolves) == 0:
        winner = "村民"
        game_over = True
    # 其他情况继续

    return {
        "winner": winner,
        "game_over": game_over
    }




