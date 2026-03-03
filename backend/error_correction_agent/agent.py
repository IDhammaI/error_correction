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

from .prompts import SPLIT_PROMPT, ORCHESTRATOR_PROMPT, CORRECTION_PROMPT
from .schemas import QuestionSplitResult, CorrectionResult
from .tools import save_questions, log_issue, split_batch
from .middleware import OCRMiddleware

load_dotenv()


def _init_model(temperature: float = 0.1, provider: str = "deepseek"):
    """初始化 LLM 模型

    Args:
        temperature: 温度参数
        provider: 模型供应商，"deepseek"（默认）或 "ernie"
    """
    provider = (provider or "deepseek").strip().lower()

    if provider == "ernie":
        api_key = os.getenv("ERNIE_API_KEY", "")
        base_url = os.getenv("ERNIE_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
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
        model_name = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
        return init_chat_model(
            model=f"deepseek:{model_name}",
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )


def create_inner_split_agent(provider: str = "deepseek"):
    """创建内层题目分割智能体

    使用 create_agent + ToolStrategy，保证结构化输出。
    无外部工具，专注于将 OCR 数据分割为 QuestionSplitResult。

    由 split_batch 工具内部调用。

    Args:
        provider: 模型供应商，"deepseek" 或 "ernie"

    Returns:
        create_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.1, provider=provider)

    return create_agent(
        model=model,
        tools=[],
        system_prompt=SPLIT_PROMPT,
        response_format=ToolStrategy(
            schema=QuestionSplitResult,
            handle_errors=True,
        ),
    )


def create_correction_agent(provider: str = "deepseek"):
    """创建内层 OCR 纠错智能体

    使用 create_agent + ToolStrategy，保证结构化输出。
    无外部工具，专注于修复 OCR 错误并输出 CorrectionResult。

    由 correct_batch 工具内部调用。

    Args:
        provider: 模型供应商，"deepseek" 或 "ernie"

    Returns:
        create_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.0, provider=provider)

    return create_agent(
        model=model,
        tools=[],
        system_prompt=CORRECTION_PROMPT,
        response_format=ToolStrategy(
            schema=CorrectionResult,
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
        middleware=[OCRMiddleware()],
    )


# 默认导出（兼容 langgraph.json 配置）
agent = create_orchestrator_agent()


if __name__ == "__main__":
    print("Orchestrator Agent 创建成功!")
