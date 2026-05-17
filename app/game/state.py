import operator
import uuid
from typing import Literal, TypedDict, List, Dict, Optional, Set, Any
from langchain_core.messages import BaseMessage
from pydantic import Field
from typing_extensions import Annotated

from app.game.game_messages import PlayerSpeechMessage

# 玩家身份类型（支持扩展）
RoleType = Literal[
    "狼人", "预言家", "女巫", "村民", "守卫", "猎人"
]

# AI玩家难度设定
AiDifficulty = Literal[
    "入门", "简单", "中等", "困难", "地狱", "不可能"
]

# AI游玩策略
AiPlayStrategy = Literal[
    "温柔",        # 少攻击、多安抚、发言温和，倾向于跟票或弃票
    "激进",        # 主动带节奏、强势踩人、频繁发起归票
    "保守",        # 求稳、少发言、不主动带节奏、投票随大流
    "欺诈",        # 擅长伪装身份、谎报信息、制造对立/反转
    "理性逻辑",    # 强调时间线、谁谁谁发言矛盾、计算票型
    "直觉感性",    # 经常用“感觉”“状态”“面相”作为理由
    "煽动情绪",    # 用感情、声势、夸张表演带动他人
    "沉默旁观",    # 很少主动发言，只在轮次末简评，投票稳健
    "跟风墙头",    # 倾向于跟随当前主流意见或者上一个发言玩家
    "自爆牺牲",    # 某些角色（如狼人）在特定轮次主动自爆或送死保队友
]

class Player(TypedDict):
    id: str # 玩家唯一标识
    name: str # 显示名称
    role: RoleType # 身份
    is_alive: bool # 是否存活
    is_human: bool # 是真实玩家还是AI
    seat: int # 座位号（固定顺序）
    difficulty: Optional[AiDifficulty] # AI玩家难度
    strategy: Optional[AiPlayStrategy] # AI游玩策略

class GameState(TypedDict):
    # 基础信息
    room_id: str # 房间号（可以线程id，保证各房间号唯一即可）
    players: List[Player] # 玩家列表
    players_config: List[dict[str, Any]] # 玩家配置列表
    alive_ids: List[str] # 当前存活的玩家列表
    phase: Literal["白天", "夜晚", "投票", "结算", "结束"]

    # 夜晚
    night_role_order: List[RoleType] # 夜晚行动顺序
    current_night_role_idx: int # 当前正在处理的夜晚角色的下标
    night_actions: Dict[str, Dict[str, str]] # key为角色类型, value是做了什么，比如：{"狼人": {"p1", "p2"}} 就是狼人玩家p1投票杀p2

    # 白天
    wait_to_speak_queue: List[str] # 尚未发言的玩家 id 队列（按座位号顺序下来）（需要存活）
    speeches: Annotated[List[PlayerSpeechMessage], operator.add] # 发言历史（采用add归约）

    # 投票
    wait_to_vote_queue: List[str] # 尚未投票玩家 id 队列
    votes: Dict[str, str] # {"p1": "p2"} 玩家p1投票给了p2
    give_up_vote_queue: List[str] # 弃权玩家 id 队列

    # 结算结果
    killed_tonight: Set[str] # 当晚死亡的玩家
    voted_out: str # 当天被投票出去的玩家
    winner: Optional[Literal["狼人", "村民"]] # 游戏胜者

    # 控制
    game_over: bool # 游戏是否已结束

    # 全局局势摘要，简要摘要累积
    global_memory: Annotated[List[str], operator.add]

    # 短期记忆
    ai_player_memory: Annotated[dict[str, List[str]], merge_personal_memory] # {"player1": ["是狼人", "你欺骗了xxxx", "把xxx投票出去了"]}

    # 预言家已查记录
    seer_checks: dict[str, dict[str, str]] # {“player1”: {"p2": "狼人", "p3": "女巫"}}

    # todo 玩家对其他玩家的印象：{player_id: {target_id: {"trust": 0.3, "suspicion": 0.6, "notes": "发言激进"}}}
    player_impressions: Dict[str, Dict[str, Any]]

    def merge_personal_memory(old: Dict[str, List[str]], new: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """合并个人记忆，保留最近50条"""
        result = old.copy()
        for pid, mems in new.items():
            if pid in result:
                result[pid].extend(mems)
                # 保留最近50条
                if len(result[pid]) > 50:
                    result[pid] = result[pid][-50:]
            else:
                result[pid] = mems
        return result