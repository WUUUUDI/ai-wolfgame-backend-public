import os

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from openai import api_key

load_dotenv()

class LLMManager:
    """LLM实例管理（单例）"""
    _instances = {}

    ds_name = "deepseek"

    @classmethod
    def get_deepseek(cls) -> ChatDeepSeek:
        if cls.ds_name not in cls._instances:
            cls._instances[cls.ds_name] = ChatDeepSeek(
                model="deepseek-chat",
                temperature=0,
                api_key=os.getenv("DS_API_KEY"),
                base_url=os.getenv("DS_BASE_URL")
            )
        return cls._instances[cls.ds_name]