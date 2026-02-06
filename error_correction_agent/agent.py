"""
错题本多智能体工厂
使用 deepagents.create_deep_agent 构建智能体，配合 ToolStrategy 实现结构化输出
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents.structured_output import ToolStrategy
from deepagents import create_deep_agent

from .prompts import SYSTEM_PROMPT
from .schemas import QuestionSplitResult
from .tools import save_questions, log_issue, download_image, read_ocr_result

load_dotenv()


def _init_model(temperature=0.1):
    """初始化 DeepSeek 模型（所有智能体共用）"""
    return init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=temperature,
    )


def create_split_agent():
    """创建题目分割智能体

    使用 deepagents 框架 + ToolStrategy 结构化输出。
    deepagents 提供文件操作、子智能体、上下文摘要等内置中间件，
    ToolStrategy 强制返回 Pydantic 校验后的 QuestionSplitResult。

    工具：save_questions, log_issue, download_image, read_ocr_result

    Returns:
        配置好的题目分割 Agent 实例 (CompiledStateGraph)
    """
    model = _init_model(temperature=0.1)

    tools = [
        save_questions,
        log_issue,
        download_image,
        read_ocr_result,
    ]

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(
            schema=QuestionSplitResult,
            handle_errors=True,
        ),
    )

    return agent


# 默认导出（兼容 langgraph.json 配置）
agent = create_split_agent()


if __name__ == "__main__":
    print("Split Agent 创建成功!")
