"""
题目处理相关工具
"""

import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.tools import tool
from config import RESULTS_DIR

load_dotenv()
logger = logging.getLogger(__name__)

@tool(parse_docstring=True)
def save_questions(questions: List[Dict[str, Any]], output_path: str = None) -> str:
    """保存分割后的题目列表到JSON文件

    将Agent分割后的题目列表保存为结构化JSON文件，供后续步骤使用。

    Args:
        questions: 题目列表，每个题目是一个字典，包含question_id、question_type、content_blocks等字段
        output_path: 输出文件路径，如果不提供则使用默认路径（RESULTS_DIR/questions.json）

    Returns:
        保存成功的文件路径
    """
    logger.info(f"save_questions called: {len(questions)} questions")
    try:
        # 使用默认路径
        if output_path is None:
            os.makedirs(RESULTS_DIR, exist_ok=True)
            output_path = os.path.join(RESULTS_DIR, "questions.json")

        # 读取已有数据（支持多次调用追加）
        existing = []
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # 合并已有数据和新数据
        all_questions = existing + questions

        # 保存JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)

        msg = f"成功保存 {len(questions)} 道题目（总计 {len(all_questions)} 道）到: {output_path}"
        logger.info(f"save_questions done: {msg}")
        return msg

    except Exception as e:
        msg = f"保存失败: {str(e)}"
        logger.error(f"save_questions error: {msg}")
        return msg


@tool(parse_docstring=True)
def log_issue(issue_type: str, description: str, block_info: Dict[str, Any] = None) -> str:
    """记录题目分割过程中遇到的问题

    当Agent在分割题目时遇到不确定或异常情况时，使用此工具记录问题，
    以便后续人工审核或改进算法。

    Args:
        issue_type: 问题类型，如 "unclear_boundary"（边界不清）、"missing_question_number"（缺少题号）、
                   "complex_structure"（复杂结构）等
        description: 问题描述，详细说明遇到的情况
        block_info: 相关block信息（可选），包含block_id、content等

    Returns:
        记录结果消息
    """
    try:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        log_path = os.path.join(RESULTS_DIR, "split_issues.jsonl")

        # 构建日志条目
        log_entry = {
            "issue_type": issue_type,
            "description": description,
        }
        if block_info:
            log_entry["block_info"] = block_info

        # 追加到JSONL文件
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return f"问题已记录: {issue_type}"

    except Exception as e:
        return f"记录失败: {str(e)}"


@tool(parse_docstring=True)
def split_batch(ocr_data: str, existing_ids: str = "") -> str:
    """对一批OCR数据进行题目分割，返回结构化题目列表JSON

    将1-2页的OCR数据发送给内层分割智能体（create_agent + ToolStrategy），
    返回经过Pydantic校验的结构化题目列表。

    Args:
        ocr_data: 一批OCR数据的JSON字符串，包含1-2页的blocks数据
        existing_ids: 前面批次已提取的题目ID列表，用逗号分隔（如 "1,2,3,4,5"），用于跳过重叠页上的已有题目

    Returns:
        题目列表的JSON字符串，如 '[{"question_id": "1", ...}, ...]'
    """
    logger.info("split_batch called")
    try:
        from ..agent import create_inner_split_agent

        inner_agent = create_inner_split_agent()

        skip_instruction = ""
        if existing_ids.strip():
            skip_instruction = f"""
**重要 - 跳过已处理的题目**：
以下题号的题目已经在前面的批次中提取过，请不要再次输出它们：{existing_ids}
只输出新的、不在上述列表中的题目。"""

        prompt = f"""请分析以下OCR识别结果，将其分割为独立的题目。

每页的数据结构：
- page_index: 页码索引
- blocks: 内容块列表，每个 block 有 block_label、block_content、block_order 三个字段

请按 page_index 和 block_order 顺序处理，返回结构化的题目列表。
{skip_instruction}

OCR数据：
{ocr_data}"""

        response = inner_agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 100},
        )

        structured = response.get("structured_response")
        if structured:
            questions = [q.model_dump() for q in structured.questions]
            logger.info(f"split_batch done: {len(questions)} questions")
            return json.dumps(questions, ensure_ascii=False)

        logger.warning("split_batch: no structured_response")
        return "[]"

    except Exception as e:
        logger.error(f"split_batch error: {str(e)}")
        return f"分割失败: {str(e)}"


@tool(parse_docstring=True)
def correct_batch(questions_json: str, ocr_context: str) -> str:
    """对一批疑似OCR错误的题目进行纠错，返回纠错后的题目列表JSON

    将标记了 needs_correction 的题目发送给内层纠错智能体（create_agent + ToolStrategy），
    返回经过Pydantic校验的纠错结果。

    Args:
        questions_json: 待纠错题目列表的JSON字符串
        ocr_context: 对应页面的原始OCR数据JSON字符串，作为纠错参考上下文

    Returns:
        纠错后的题目列表JSON字符串
    """
    logger.info("correct_batch called")
    try:
        from ..agent import create_correction_agent

        correction_agent = create_correction_agent()

        prompt = f"""请修复以下题目中的 OCR 错误。

## 待纠错题目
{questions_json}

## 原始 OCR 参考数据
以下是这些题目对应页面的原始 OCR block 数据，可作为纠错参考：
{ocr_context}

请逐题修复标记的 OCR 问题，输出纠错后的结构化数据。"""

        response = correction_agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 100},
        )

        structured = response.get("structured_response")
        if structured:
            corrected = [q.model_dump() for q in structured.corrected_questions]
            logger.info(f"correct_batch done: {len(corrected)} questions corrected")
            return json.dumps(corrected, ensure_ascii=False)

        logger.warning("correct_batch: no structured_response")
        return "[]"

    except Exception as e:
        logger.error(f"correct_batch error: {str(e)}")
        return f"纠错失败: {str(e)}"
