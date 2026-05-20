import random
import re
from typing import Dict, Any, Optional

from pip._internal.resolution.resolvelib import candidates
from pydantic import Field, BaseModel

from app.game.players.base import BasePlayer
from app.game.state import GameState, AiDifficulty, AiPlayStrategy
from llm import LLMManager

class VoteAction(BaseModel):
    target_id: str = Field(description="要投票的玩家ID，例如 'p1'")

class KillAction(BaseModel):
    target_id: str = Field(description="要击杀的玩家ID，例如 'p3'")

class SeerCheckAction(BaseModel):
    target_id: str = Field(description="要查验的玩家ID，例如 'p3'")

class SpeakAction(BaseModel):
    content: str = Field(description="发言内容，不少于50中文字，最多100中文字", max_length=500)

class WitchAction(BaseModel):
    use_antidote: bool = False
    use_poison: bool = False
    target_id: str = Field(description="要救或毒的目标玩家ID, 例如'p4'")

class GuardAction(BaseModel):
    target_id: str = Field(description="要保护的玩家ID，例如'p5'")

class HunterShotAction(BaseModel):
    target_id: str = Field(description="要射杀的玩家ID, 例如'p6'")


class AIPlayer(BasePlayer):

    def __init__(self, player_id:str):
        self.id = player_id

    async def get_action(self, state: GameState, action_type: str, context: None) -> Any:

        # 获取自身信息
        players = state["players"]
        myself = next((p for p in state["players"] if p["id"] == self.id), None)
        if not myself or not myself["is_alive"]:
            return None

        role = myself["role"]
        difficulty = myself["difficulty"]
        strategy = myself["strategy"]

        # 获取全局记忆（最近的5条）
        global_mem = state.get("global_memory", [])
        recent_global = global_mem[-5:] if global_mem else None

        # 获取个人记忆（最近5条）
        personal_mem = state.get("ai_player_memory", {}).get(self.id, [])
        recent_personal = personal_mem[-5:] if personal_mem else None

        # 获取原始对话，补充细节（最近8条）
        speeches = state.get("speeches", [])
        recent_speeches = speeches[-5:] if speeches else None
        speech_text = "\n".join([
            f"{s.get('player_id', '?')}：{s.get('content', '')}"
            for s in recent_speeches
        ])

        # 本局设定的初始所有角色身份
        available_roles = state.get("available_roles", [])

        # 获取额外信息（狼人队友、预言家已验对象）
        extra_info = self._get_role_extra_info(state, myself)

        # todo 获取玩家对其他玩家的印象
        # impressions = state.get("player_impressions", {}).get(self.id, {})
        # impression_text = ""
        # if impressions:
        #     lines = []
        #     for target_id, data in impressions.items():
        #         trust = data.get("trust", 0)
        #         suspicion = data.get("suspicion", 0)
        #         notes = data.get("notes", "")
        #         if notes:
        #             lines.append(f"对 {target_id} 的印象: {notes} (信任度 {trust:.2f}, 怀疑度 {suspicion:.2f})")
        #         else:
        #             lines.append(f"对 {target_id} 的印象: 信任度 {trust:.2f}, 怀疑度 {suspicion:.2f}")
        #         impression_text = "\n".join(lines) if lines else "暂无其他玩家的印象"
        # else:
        #     impression_text = "暂无其他玩家的印象"

        # 构造系统提示
        global_text = "\n".join(recent_global) if recent_global else "暂无全局摘要"
        personal_text = "\n".join(recent_personal) if recent_personal else "暂无个人记忆"

        system_prompt = f"""
        你的游戏id为:{self.id}, 角色是:{role}。你在跟其他的玩家一起游玩狼人杀,总人数为:{len(players)}, 目前存活人数:{len(state["alive_ids"])}。
        你需要展示出的水平是:{difficulty}, 你的游玩策略是:{strategy}
        
        【重要游戏规则】
        - 如果你的身份是【预言家】，如果没有明确的带队把握或者局势紧张的情况下，请你不要轻易暴露自己的身份，除非很有把握能赢下比赛的情况下，你可以暴露身份并且带队。
        - 发言要结合你的策略和当前局势以及被设定的难度，不要无意义地重复。
        - 不要编造不存在的信息！！！
        
        【存活玩家的id】
        {state["alive_ids"]}
        
        【本局包含的所有角色身份】
        {available_roles}
        
        【最近全局局势摘要】
        {global_text}
        
        【你的最近个人记忆】
        {personal_text}
        
        【角色额外信息】
        {extra_info}
        
        【最近发言记录】
        {speech_text}
        
        【注意】
        你的发言和决策一定要根据'决策', '设定难度', '局势', '个人发言'，做出最符合你角色和策略的行动和发言！
        
"""

        # 根据行动类型构造用户提示
        a_type = action_type.lower()

        candidates = context.get("candidates", [])
        if not candidates and a_type != "speak":
            return None


        if a_type == "night_kill":
            team_votes = context.get("team_vote", {})
            extra_note = ""

            if team_votes:
                selections = []
                for pid, target in team_votes.items():
                    teammate = next((p for p in players if p["id"] == pid), None)
                    name = teammate["name"] if teammate else pid
                    selections.append(f"{name}({pid}) 选择了击杀 {target}")
                extra_note = "你的队友已经选择了以下目标：\n" + "\n".join(selections) + "\n你可以选择跟随其中任意一个，也可以坚持自己的判断，但是需要保证选出来一定能够出局一个玩家。"
            else:
                extra_note = "你是第一个行动的狼人，请自由选择击杀目标。"

            user_prompt = f"夜晚阶段, 你的身份是{role}, 请选择要击杀的玩家（只能从列表当中选）。\n候选人:{candidates}\n{extra_note}\n只能输出玩家ID（从候选人中的元素选择）。"
        elif a_type == "vote":
            user_prompt = f"投票阶段, 请根据局势以及大家的发言以及所选择的决策，从候选人中选出你要投票的玩家ID。\n候选人:{candidates}\n只输出玩家ID。"
        elif a_type == "speak":
            user_prompt = f"发言阶段, 你的身份是:{role} \n请发表你的观点(根据你自身的设定和局势分析，可以表水、踩人、分析等等)。\n发言请尽量丰富，至少50字以上，以展现你的思考和策略。"
        elif a_type == "seer_check":
            user_prompt = f"查验阶段，你的身份是{role}, 请选择要查验的玩家（只能从列表中选择）。\n 候选人:{candidates}\n只能输出玩家ID（如：从候选人中的元素选择）。"
        elif a_type == "witch_action":
            has_antidote = context.get("witch_has_antidote", True)
            has_poison = context.get("witch_has_poison", True)
            wolf_target = context.get("wolf_target", None)
            wolf_info = f"狼人今晚击杀了：{wolf_target}" if wolf_target else "今晚平安夜（无人被刀）"
            user_prompt = f"""女巫夜晚行动阶段，你的身份是{role}。
            {wolf_info}
            你拥有解药（{'可用' if has_antidote else '已用'}）和毒药（{'可用' if has_poison else '已用'}）。
            候选人（可救/可毒的对象）：{candidates}

            请根据局势决定：
            - 如果使用解药救人（通常救狼人击杀的目标），请设置 use_antidote=True，target_id 为被救玩家ID。
            - 如果使用毒药杀人，请设置 use_poison=True，target_id 为你要毒杀的玩家ID。
            - 如果都不使用，请设置 use_antidote=False, use_poison=False，target_id 可以是空字符串或 None。

            注意：解药和毒药每局只能各用一次，请谨慎选择。"""


        elif a_type == "guard_action":
            user_prompt = f"守卫行动阶段，你的身份是{role}, 请从下方候选人中选择要守卫的玩家。\n候选人:{candidates}\n选择后放入到参数'target_id'中"
        elif a_type == "hunter_shot_action":
            user_prompt = f"猎人开枪阶段，你的身份是{role}, 你已出局，现在需要你在出局之前朝一名玩家开枪，请从下方候选人中选择开枪对象:\n{candidates}"
        else:
            return None

        ds_model = LLMManager.get_deepseek()

        messages = [{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}]

        # print(f"[debug], role:{role}, extra_info:{extra_info}, system_prompt:{system_prompt}, user_prompt:{user_prompt}")

        # 调用大模型
        try:
            if a_type == "night_kill":
                ds_structured = ds_model.with_structured_output(KillAction)
                response = ds_structured.invoke(messages)
                return response.target_id
            elif a_type == "vote":
                ds_structured = ds_model.with_structured_output(VoteAction)
                response = ds_structured.invoke(messages)
                return response.target_id
            elif a_type == "seer_check":
                ds_structured = ds_model.with_structured_output(VoteAction)
                response = ds_structured.invoke(messages)
                return response.target_id
            elif a_type == "speak":
                ds_structured = ds_model.with_structured_output(SpeakAction)
                response = ds_structured.invoke(messages)
                return response.content
            elif a_type == "witch_action":
                ds_structured = ds_model.with_structured_output(WitchAction)
                response = ds_structured.invoke(messages)
                print(f"女巫的response:{response}")
                return {
                    "use_antidote": response.use_antidote,
                    "use_poison": response.use_poison,
                    "target_id": response.target_id
                }
            elif a_type == "guard_action":
                ds_structured = ds_model.with_structured_output(GuardAction)
                response = ds_structured.invoke(messages)
                return response.target_id
            elif a_type == "hunter_shot_action":
                ds_structured = ds_model.with_structured_output(HunterShotAction)
                response = ds_structured.invoke(messages)
                return response.target_id

        except Exception as e:
            print(f"LLM调用失败：{e}, 回退随机决策")
            return self._fallback_action(state, action_type, context)

        return None

    def _get_role_extra_info(self, state: GameState, myself: Dict[str, Any]) -> str:
        role = myself["role"]
        if role == "狼人":
            teammates = [
                p["id"] for p in state["players"]
                if p["role"] == "狼人" and p["id"] != self.id and p["is_alive"]
            ]
            return f"你的狼人队友（存活）：{teammates}" if teammates else "你没有存活着的队友"
        elif role == "预言家":
            checks = state.get("seer_checks", {}).get(self.id, {})

            if checks:
                check_str = ", ".join([f"{tid}是{role}" for tid, role in checks.items()])
                return f"你之前的查验结果是:{check_str}"

            return "你之前还没有查验"

        return ""

    def _fallback_action(self, state: GameState, action_type: str, context: Dict[str, Any]) -> Any:
        """"LLM调用失败时兜底策略"""
        a_type = action_type.lower()
        if a_type == "vote":
            candidates = context.get("candidates", [])
            return random.choice(candidates) if candidates else None
        elif a_type == "speak":
            return "(AI随机发言)"
        elif a_type == "night_kill":
            return random.choice(state["alive_ids"])

        return None