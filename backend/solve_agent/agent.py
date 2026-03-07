"""
解题智能体

调用 LLM 对结构化题目进行解答，返回结构化解题结果。
"""

import json
import logging
from typing import List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from llm import init_model
from .prompts import SOLVE_PROMPT
from .schemas import SolveBatchResult

logger = logging.getLogger(__name__)


def invoke_solve(questions: List[Dict[str, Any]], provider: str = "deepseek") -> SolveBatchResult:
    """对一批题目进行解答

    Args:
        questions: 题目列表（Question schema 格式的 dict）
        provider: 模型供应商，"deepseek" 或 "ernie"

    Returns:
        SolveBatchResult 结构化解题结果
    """
    model = init_model(temperature=0.0, provider=provider)
    structured_model = model.with_structured_output(SolveBatchResult)

    prompt = f"""请解答以下题目，返回每道题的答案和解题过程。

题目数据：
{json.dumps(questions, ensure_ascii=False, indent=2)}"""

    result = structured_model.invoke([
        SystemMessage(content=SOLVE_PROMPT),
        HumanMessage(content=prompt),
    ])

    logger.info(f"invoke_solve done: {len(result.results)} answers (provider={provider})")
    return result
