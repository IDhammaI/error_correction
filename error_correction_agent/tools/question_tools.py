"""
题目处理相关工具
"""

import os
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


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
    try:
        # 使用默认路径
        if output_path is None:
            results_dir = os.getenv("RESULTS_DIR", "results")
            os.makedirs(results_dir, exist_ok=True)
            output_path = os.path.join(results_dir, "questions.json")

        # 保存JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

        return f"成功保存 {len(questions)} 道题目到: {output_path}"

    except Exception as e:
        return f"保存失败: {str(e)}"


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
        results_dir = os.getenv("RESULTS_DIR", "results")
        os.makedirs(results_dir, exist_ok=True)
        log_path = os.path.join(results_dir, "split_issues.jsonl")

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
