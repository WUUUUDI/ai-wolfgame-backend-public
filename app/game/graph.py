import asyncio
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.game.state import GameState
from app.game.nodes.init_game import init_game
from app.game.nodes.judge_broadcast import judge_broadcast, router_after_broadcast
from app.game.nodes.night_actions import process_night_role, should_continue_night
from app.game.nodes.night_resolve import night_resolve, after_night
from app.game.nodes.day_speech import process_speech, should_continue_speech
from app.game.nodes.vote import cast_vote, should_continue_vote
from app.game.nodes.vote_resolve import vote_resolve
from app.game.nodes.check_winner import check_winner

# ---------------------------
# 辅助节点：准备投票队列
# ---------------------------
def prepare_vote(state: GameState) -> dict:
    """在白天发言结束后，将存活玩家列表设为投票队列，并清空旧的投票记录"""
    return {
        "wait_to_vote_queue": state["alive_ids"][:],   # 复制存活玩家列表
        "votes": {},
        "give_up_vote_queue": []
    }

# ---------------------------
# 条件路由：游戏未结束时回到广播，否则结束
# ---------------------------
def after_winner(state: GameState) -> Literal["judge_broadcast", END]:
    if state["game_over"]:
        return END
    else:
        return "judge_broadcast"

# ---------------------------
# 构建图
# ---------------------------
graph_builder = StateGraph(GameState)

# 添加所有节点
graph_builder.add_node("init_game", init_game)
graph_builder.add_node("judge_broadcast", judge_broadcast)
graph_builder.add_node("process_night_role", process_night_role)
graph_builder.add_node("night_resolve", night_resolve)
graph_builder.add_node("process_speech", process_speech)
graph_builder.add_node("prepare_vote", prepare_vote)
graph_builder.add_node("cast_vote", cast_vote)
graph_builder.add_node("vote_resolve", vote_resolve)
graph_builder.add_node("check_winner", check_winner)

# 入口：初始化 -> 广播
graph_builder.add_edge(START, "init_game")
graph_builder.add_edge("init_game", "judge_broadcast")
graph_builder.add_edge("prepare_vote", "cast_vote")

# 广播后的条件路由（根据 phase 决定下一阶段）
graph_builder.add_conditional_edges(
    "judge_broadcast",
    router_after_broadcast,
    {
        "process_night_role": "process_night_role",
        "process_speech": "process_speech"
    }
)

# 夜晚行动循环
graph_builder.add_conditional_edges(
    "process_night_role",
    should_continue_night,
    {
        "process_night_role": "process_night_role",
        "night_resolve": "night_resolve"
    }
)

graph_builder.add_conditional_edges(
    "night_resolve",
    after_night,
    {
        "judge_broadcast": "judge_broadcast",
        END: END
    }
)# 夜晚结算后回到广播（白天）

# 白天发言循环
graph_builder.add_conditional_edges(
    "process_speech",
    should_continue_speech,
    {
        "process_speech": "process_speech",
        "prepare_vote": "prepare_vote"   # 发言结束则准备投票
    }
)

# 投票阶段循环
graph_builder.add_conditional_edges(
    "cast_vote",
    should_continue_vote,
    {
        "cast_vote": "cast_vote",
        "vote_resolve": "vote_resolve"
    }
)

# 投票结算后检查胜负
graph_builder.add_edge("vote_resolve", "check_winner")

# 胜负判定后：未结束则回到广播（新的一轮），结束则终止
graph_builder.add_conditional_edges(
    "check_winner",
    after_winner,
    {
        "judge_broadcast": "judge_broadcast",
        END: END
    }
)

# ---------------------------
# 编译与执行
# ---------------------------
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# 初始状态（留空 players，由 init_game 生成测试数据）
initial_state = {
    "room_id": "room_001",
    "players": [],
    "alive_ids": [],
    "phase": "夜晚",
    "night_role_order": [],
    "current_night_role_idx": 0,
    "night_actions": {},
    "wait_to_speak_queue": [],
    "speeches": [],
    "wait_to_vote_queue": [],
    "votes": {},
    "give_up_vote_queue": [],
    "killed_tonight": set(),
    "voted_out": "",
    "winner": None,
    "game_over": False,
}

config = {"configurable": {"thread_id": "1", "user_id": "1"}}

async def main():
    async for chunk in graph.astream(initial_state, config, stream_mode="updates"):
        print(chunk)

if __name__ == "__main__":
    asyncio.run(main())