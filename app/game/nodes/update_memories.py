from typing import Dict, Any

import llm
from app.game.state import GameState


async def update_memories(state: GameState) -> Dict[str, Any]:
    """更新全局记忆和个人记忆"""
    round_num = len(state.get("global_memory", [])) + 1
    alive_ids = state["alive_ids"]
    killed_tonight = state.get("killed_tonight", set())
    voted_out = state.get("voted_out", "")
    recent_speeches = state.get("speeches", [])[-10:] #最近10条原始发言
    # print(f"recent_speeches: {recent_speeches}")
    # 格式化发言文本
    speech_text = []
    for s in recent_speeches:
        if hasattr(s, "player_id") and hasattr(s, "role") and hasattr(s, "content"):
            pid = s.player_id
            role = s.role
            content = s.content
        elif isinstance(s, dict):  # 字典
            pid = s.get('player_id', '?')
            role = s.get('role', '?')
            content = s.get('content', '') or ""
        else:
            continue
        speech_text.append(f"{pid}({role})：{content}")

    # 生成全局局势摘要
    global_prompt = f"""你是狼人杀游戏裁判, 请生成一句简洁的全局局势摘要(不要漏掉关键信息)(不超过50字)
当前第{round_num}结束。
存活玩家ID列表:{alive_ids}
昨晚死亡:{killed_tonight}
今天被放逐:{voted_out if voted_out else '无'}
最近发言摘要:
{speech_text}
只输出摘要，不要有其他内容。
"""

    ds = llm.LLMManager.get_deepseek()

    try:
        resp = await ds.ainvoke([{"role": "user", "content": global_prompt}])
        global_summary = resp.content.strip()
    except Exception as e:
        print(f"生成全局摘要失败:{e}")
        global_summary = f"第{round_num}轮结束, 存活{alive_ids}, 放逐{voted_out}, 死亡{killed_tonight}"

    # 为每个存活玩家生成个人记忆
    personal_updates = {}
    for pid in alive_ids:
        player = next((p for p in state["players"] if p["id"] == pid), None)
        role = player["role"]
        vote_target = state.get("votes", {}).get(pid, None)
        personal_prompt = f"""你是{role}玩家{pid}。请基于以下信息，写下一句你当下的内心独白或对局势的看法（不超50字）：
当前局势:存活{alive_ids}, 昨晚死亡{killed_tonight}, 今天放逐{voted_out}。
你投票给了{vote_target if vote_target else '弃权'}。
最近发言:{speech_text}
只输出一句话，不要有多余内容"""
        try:
            resp = await ds.ainvoke([{"role": "user", "content": personal_prompt}])
            memory_entry = resp.content.strip()
        except Exception as e:
            print(f"生成{pid}个人记忆失败:{e}")
            memory_entry = f"我是{role}, 本轮无事发生"
        personal_updates[pid] = [memory_entry]

        return {
            "global_summary": [global_summary],
            "ai_player_memory": personal_updates
        }
