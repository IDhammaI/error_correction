"""
公共 LLM 初始化工具

所有智能体模块共享的模型初始化逻辑，避免重复代码。
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()


def init_model(temperature: float = 0.1, provider: str = "deepseek", model_name: str = None):
    """初始化 LLM 模型

    Args:
        temperature: 温度参数
        provider: 模型供应商，"deepseek"（默认）或 "ernie"
        model_name: 指定模型名称，为 None 时使用环境变量默认值
    """
    provider = (provider or "deepseek").strip().lower()

    if provider == "ernie":
        api_key = os.getenv("ERNIE_API_KEY", "")
        base_url = os.getenv("ERNIE_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
        if model_name is None:
            model_name = os.getenv("ERNIE_MODEL_NAME", "ernie-4.5-turbo-128k-preview")

        if not api_key:
            raise ValueError("使用文心一言需要配置 ERNIE_API_KEY 环境变量")

        return init_chat_model(
            model=model_name,
            model_provider="openai",
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
        )
    else:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        if model_name is None:
            model_name = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
        return init_chat_model(
            model=f"deepseek:{model_name}",
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )
