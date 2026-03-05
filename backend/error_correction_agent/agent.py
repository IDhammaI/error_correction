"""
错题本智能体工厂
- 内层：create_agent (langchain) + ToolStrategy — 结构化输出题目分割结果
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import SystemMessage, HumanMessage

from .prompts import SPLIT_PROMPT, SPLIT_PROMPT_LITE, CORRECTION_PROMPT
from .schemas import QuestionSplitResult, CorrectionResult

load_dotenv()


def _init_model(temperature: float = 0.1, provider: str = "deepseek", model_name: str = None):
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


def detect_subject_via_llm(ocr_text_sample: str, db_subjects: list, provider: str = "deepseek") -> str:
    """通过轻量 LLM 识别试卷科目

    Args:
        ocr_text_sample: 前几页 OCR 文本拼接
        db_subjects: 数据库已有科目列表
        provider: 模型供应商

    Returns:
        识别出的科目名称，失败时返回空字符串
    """
    provider = (provider or "deepseek").strip().lower()

    # 读取轻量模型名（未配置则为 None，回退默认模型）
    if provider == "ernie":
        light_model = os.getenv("ERNIE_LIGHT_MODEL_NAME")
    else:
        light_model = os.getenv("DEEPSEEK_LIGHT_MODEL_NAME")

    model = _init_model(temperature=0.0, provider=provider, model_name=light_model)

    existing = '、'.join(db_subjects) if db_subjects else '无'
    prompt = (
        f'已有科目列表：{existing}\n\n'
        f'以下是一份试卷的 OCR 文字节选：\n{ocr_text_sample[:1500]}\n\n'
        '判断试卷科目，输出格式【学段+科目】。'
        '学段：小学/初中/高中/大学；未标注学段不默认，直接用“未知学段”。'
        '科目可能包含大学课程（如高等数学、线性代数、概率论、大学物理、数据结构等）。'
        '只输出结果，不要引号/解释/换行；无法判断输出“未知”。'
    )

    response = model.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()

    if not result or '未知' in result:
        return ""

    return result


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


def invoke_split(prompt: str, provider: str = "deepseek"):
    """统一调用分割，屏蔽 ToolStrategy vs with_structured_output 差异

    Args:
        prompt: 用户 prompt
        provider: 模型供应商

    Returns:
        QuestionSplitResult 或 None
    """
    if provider == "ernie":
        model = _init_model(temperature=0.1, provider=provider)
        structured_model = model.with_structured_output(QuestionSplitResult)
        return structured_model.invoke([
            SystemMessage(content=SPLIT_PROMPT_LITE),
            HumanMessage(content=prompt),
        ])
    else:
        agent = create_inner_split_agent(provider=provider)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 100},
        )
        return response.get("structured_response")


def invoke_correction(prompt: str, provider: str = "deepseek"):
    """统一调用纠错，屏蔽 ToolStrategy vs with_structured_output 差异

    Args:
        prompt: 用户 prompt
        provider: 模型供应商

    Returns:
        CorrectionResult 或 None
    """
    if provider == "ernie":
        model = _init_model(temperature=0.0, provider=provider)
        structured_model = model.with_structured_output(CorrectionResult)
        return structured_model.invoke([
            SystemMessage(content=CORRECTION_PROMPT),
            HumanMessage(content=prompt),
        ])
    else:
        agent = create_correction_agent(provider=provider)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 100},
        )
        return response.get("structured_response")


