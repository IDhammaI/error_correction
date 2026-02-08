"""
错题本多智能体工厂
- 外层：create_deep_agent (deepagents) — 编排分批策略、调用工具
- 内层：create_agent (langchain) + ToolStrategy — 结构化输出题目分割结果
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from deepagents import create_deep_agent

from .prompts import SPLIT_PROMPT, ORCHESTRATOR_PROMPT
from .schemas import QuestionSplitResult
from .tools import save_questions, log_issue, split_batch

load_dotenv()


def _init_model(temperature=0.1):
    """初始化 DeepSeek 模型（所有智能体共用）"""
    return init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=temperature,
    )


def create_inner_split_agent():
    """创建内层题目分割智能体

    使用 create_agent + ToolStrategy，保证结构化输出。
    无外部工具，专注于将 OCR 数据分割为 QuestionSplitResult。

    由 split_batch 工具内部调用。

    Returns:
        create_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.1)

    return create_agent(
        model=model,
        tools=[],
        system_prompt=SPLIT_PROMPT,
        response_format=ToolStrategy(
            schema=QuestionSplitResult,
            handle_errors=True,
        ),
    )


def create_orchestrator_agent():
    """创建外层编排智能体

    使用 deepagents 框架，自主决定分批策略并循环调用工具。
    不设 response_format — 外层只需文本回复，结构化输出由内层保证。

    工具：
        - split_batch: 调用内层 agent 进行题目分割（结构化输出）
        - save_questions: 追加保存题目到 JSON 文件
        - log_issue: 记录分割问题

    Returns:
        create_deep_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.1)

    tools = [
        split_batch,
        save_questions,
        log_issue,
    ]

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=ORCHESTRATOR_PROMPT,
    )


# 默认导出（兼容 langgraph.json 配置）
agent = create_orchestrator_agent()


if __name__ == "__main__":
    print("Orchestrator Agent 创建成功!")
