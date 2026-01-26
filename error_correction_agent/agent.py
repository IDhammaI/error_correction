"""
错题本题目分割Agent
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from .prompts import SYSTEM_PROMPT
from .tools import save_questions, log_issue, download_image, read_ocr_result

load_dotenv()


def create_question_split_agent():
    """创建题目分割Agent

    使用DeepSeek模型和定义的工具创建一个专门用于分割题目的Agent。

    Returns:
        配置好的Agent实例
    """
    # 初始化模型（DeepSeek）
    model = init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=0.1,  # 低温度以获得更确定性的输出
    )

    # 定义工具列表
    tools = [
        save_questions,
        log_issue,
        download_image,
        read_ocr_result,
    ]

    # 创建Agent
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


# 导出agent实例（用于langgraph.json）
agent = create_question_split_agent()


if __name__ == "__main__":
    # 测试Agent创建
    print("Agent创建成功!")
    print(f"工具列表: {[tool.name for tool in agent.tools]}")
