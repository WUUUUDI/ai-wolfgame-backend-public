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
    content: str = Field(description="发言内容，不超过100字", max_length=100)


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

        system_prompt = f"""你是玩家{self.id}, 角色是:{role}。你在跟其他的玩家一起游玩狼人杀,总人数为:{len(players)}, 目前存活人数:{len(state["alive_ids"])}。
        你需要展示出的水平是:{difficulty}, 你的游玩策略是:{strategy}
        
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
        
        注意：你的发言和决策一定要根据'决策', '设定难度', '局势', '个人发言'，做出最符合你角色和策略的行动和发言。
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
            user_prompt = f"发言阶段, 请发表你的观点(根据你自身的设定和局势分析，可以表水、踩人、分析等等)。发言要精简，不要超过60字。"
        elif a_type == "seer_check":
            user_prompt = f"查验阶段，你是{role}, 请选择要查验的玩家（只能从列表中选择）。\n 候选人:{candidates}\n智能输出玩家ID（如：从候选人中的元素选择）。"
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