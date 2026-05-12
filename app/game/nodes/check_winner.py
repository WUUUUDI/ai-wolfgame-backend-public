from app.game.state import GameState


async def check_winner(state: GameState) -> dict:
    """根据存活玩家判断胜利阵营"""

    players = state["players"]
    alive_role = [r["role"] for r in players if r["is_alive"]]

    # print(f"alive:{state['alive_ids']}")

    werewolf_alive = any(r == "狼人" for r in alive_role)
    villager_alive = any(r in ["村民", "预言家", "女巫"] for r in alive_role)

    # print(f"al{werewolf_alive}, vl{villager_alive}")

    game_over = False

    if not werewolf_alive:
        winner = "村民"
        game_over = True
    elif not villager_alive:
        winner = "狼人"
        game_over = True
    else:
        winner = None
        game_over = False

    return {
        "winner": winner,
        "game_over": game_over
    }




