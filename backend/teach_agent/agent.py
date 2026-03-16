"""
教学辅导智能体 — 流式多轮对话
"""

import logging
from typing import Generator, List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm import init_model
from .prompts import build_teach_prompt

logger = logging.getLogger(__name__)


def _build_question_text(question: Dict[str, Any]) -> str:
    """从 Question ORM 序列化数据中提取题目文本"""
    parts = []

    q_type = question.get("question_type", "")
    if q_type:
        parts.append(f"【{q_type}】")

    content_json = question.get("content_json")
    if isinstance(content_json, list):
        for block in content_json:
            if block.get("block_type") == "text":
                parts.append(block.get("content", ""))
            elif block.get("block_type") == "image":
                parts.append(f"[图片: {block.get('content', '')}]")

    options_json = question.get("options_json")
    if isinstance(options_json, list):
        for opt in options_json:
            parts.append(opt)

    return "\n".join(parts)


def stream_teach(
    *,
    question: Dict[str, Any],
    messages: List[Dict[str, str]],
    provider: str = "openai",
    model_name: str | None = None,
) -> Generator[str, None, None]:
    """流式教学对话

    Args:
        question: 题目数据（含 content_json, options_json, answer, question_type,
                  subject, knowledge_tags 等字段）
        messages: 对话历史 [{"role": "user"|"assistant", "content": "..."}]
        provider: 模型供应商
        model_name: 指定模型名称，为 None 时使用 provider 默认模型

    Yields:
        逐 token 的文本片段
    """
    subject = question.get("subject") or "未知科目"
    knowledge_tags = question.get("knowledge_tags") or []
    answer_text = question.get("answer") or "暂无答案"
    question_text = _build_question_text(question)

    system_prompt = build_teach_prompt(
        subject=subject,
        knowledge_tags=knowledge_tags,
        question_text=question_text,
        answer_text=answer_text,
    )

    # 构建 LangChain 消息列表
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    model = init_model(temperature=0.4, provider=provider, model_name=model_name)

    for chunk in model.stream(lc_messages):
        token = chunk.content
        if token:
            yield token
