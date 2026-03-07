"""
解题智能体

调用 LLM 对结构化题目进行解答，返回结构化解题结果。
"""

import json
import logging
import re
from typing import List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from llm import init_model
from .prompts import SOLVE_PROMPT
from .schemas import SolveResult, SolveBatchResult

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def invoke_solve(questions: List[Dict[str, Any]], provider: str = "deepseek") -> SolveBatchResult:
    """对一批题目进行解答

    Args:
        questions: 题目列表（Question schema 格式的 dict）
        provider: 模型供应商，"deepseek" 或 "ernie"

    Returns:
        SolveBatchResult 结构化解题结果
    """
    model = init_model(temperature=0.0, provider=provider)

    prompt = f"""请解答以下题目，返回每道题的答案和解题过程。

题目数据：
{json.dumps(questions, ensure_ascii=False, indent=2)}"""

    messages = [
        SystemMessage(content=SOLVE_PROMPT),
        HumanMessage(content=prompt),
    ]

    # 尝试结构化输出
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            structured_model = model.with_structured_output(SolveBatchResult)
            result = structured_model.invoke(messages)
            if result is not None:
                logger.info(f"invoke_solve done: {len(result.results)} answers (provider={provider})")
                return result
            logger.warning(f"structured_output 返回 None，尝试 {attempt}/{MAX_RETRIES}")
        except Exception as e:
            logger.warning(f"structured_output 失败 ({attempt}/{MAX_RETRIES}): {e}")

    # 回退：用普通文本输出，手动解析答案
    logger.info("回退到纯文本模式解析答案")
    response = model.invoke(messages)
    text = response.content

    results = _parse_answers_from_text(text, questions)
    batch = SolveBatchResult(results=results)
    logger.info(f"invoke_solve (fallback) done: {len(batch.results)} answers (provider={provider})")
    return batch


def _parse_answers_from_text(text: str, questions: List[Dict]) -> List[SolveResult]:
    """从纯文本响应中解析每道题的答案"""
    results = []
    for q in questions:
        qid = q["question_id"]
        # 尝试从文本中找到该题的答案
        answer = _extract_answer_for_question(text, qid, q)
        results.append(SolveResult(
            question_id=qid,
            answer=answer,
            reasoning=text[:200] if len(results) == 0 else "",
            confidence=0.5,
        ))
    return results


def _extract_answer_for_question(text: str, qid: str, question: Dict) -> str:
    """从文本中提取特定题目的答案"""
    # 提取题号中的数字部分
    local_id = qid.rsplit("_", 1)[-1] if "_" in qid else qid

    # 常见格式: "第1题：A" "1. A" "题1: A" "{qid}: A"
    patterns = [
        rf"(?:题\s*)?{re.escape(local_id)}[\.、:：\s]+\s*([A-D])\b",
        rf"{re.escape(qid)}[\.、:：\s]+\s*([A-D])\b",
        rf"(?:答案|选)\s*[:：]?\s*([A-D])\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).upper()

    # 最后兜底：找文本中出现的第一个独立 A/B/C/D
    match = re.search(r"\b([A-D])\b", text)
    return match.group(1).upper() if match else "A"
