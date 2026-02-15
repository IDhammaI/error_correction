"""
错题本生成工作流 - LangGraph 实现
使用 StateGraph 将每个处理步骤定义为图节点
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, TypedDict
from dotenv import load_dotenv
from rich.console import Console
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from config import RESULTS_DIR
from .utils import prepare_input, export_wrongbook

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNTIME_ROOT = os.path.join(BACKEND_ROOT, "runtime_data")

load_dotenv()
console = Console()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('workflow.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ── 状态定义 ──────────────────────────────────────────────


class WorkflowState(TypedDict, total=False):
    """工作流全局状态"""
    file_paths: List[str]                # 输入文件路径列表（支持多文件）
    image_paths: List[str]               # 标准化后的图片路径列表
    questions: List[Dict[str, Any]]      # 分割后的题目列表
    selected_ids: List[str]              # 用户选中的题目 ID
    output_path: str                     # 导出文件路径


# ── 节点函数 ──────────────────────────────────────────────


def prepare_input_node(state: WorkflowState) -> dict:
    """节点: 准备输入（PDF/图片 → 标准化图片列表），支持多文件"""
    console.print("[bold yellow]步骤 1: 准备输入文件[/bold yellow]")
    step_start = time.time()

    file_paths = state["file_paths"]
    all_image_paths = []
    for fp in file_paths:
        all_image_paths.extend(prepare_input(fp))

    logger.info(f"步骤1完成: 准备输入文件，共 {len(all_image_paths)} 张图片（来自 {len(file_paths)} 个文件），耗时 {time.time() - step_start:.2f}s")
    return {"image_paths": all_image_paths}


def split_questions_node(state: WorkflowState) -> dict:
    """节点: Agent 智能分割题目

    OCR 解析由编排智能体的 OCRMiddleware 自动完成。
    workflow 只需将图片路径传给 agent，中间件会：
    1. 调用 PaddleOCR API 解析图片
    2. 简化结果并注入 messages
    3. agent 自主分批调用 split_batch + save_questions
    """
    console.print("[bold yellow]步骤 2: Agent OCR + 分割题目[/bold yellow]")
    step_start = time.time()

    results_dir = RESULTS_DIR
    os.makedirs(results_dir, exist_ok=True)

    from error_correction_agent.agent import create_orchestrator_agent

    logger.info("开始调用编排智能体（OCR + 分割）")
    agent = create_orchestrator_agent()

    image_paths = state["image_paths"]

    # 清空旧的 questions.json（外层 agent 通过 save_questions 追加写入）
    questions_file = os.path.join(results_dir, "questions.json")
    if os.path.exists(questions_file):
        os.remove(questions_file)

    console.print(f"[cyan]Agent 输入: {len(image_paths)} 张图片[/cyan]")

    # 传入图片路径 JSON，OCRMiddleware 会自动解析并注入 OCR 结果
    agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "请对以下图片进行 OCR 解析并分割题目。"},
                {"role": "user", "content": json.dumps(image_paths, ensure_ascii=False)}
            ]
        },
        config={"recursion_limit": 300},
    )

    # 从文件读取结果（外层 agent 通过 save_questions 追加保存）
    questions = []
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)

    if questions:
        logger.info(f"Agent分割完成: 共 {len(questions)} 道题目，耗时 {time.time() - step_start:.2f}s")
        console.print(f"[green]✓ 成功分割 {len(questions)} 道题目[/green]")
    else:
        logger.warning("Agent未生成任何题目，请检查执行日志")
        console.print("[yellow]⚠ Agent未生成任何题目[/yellow]")

    return {"questions": questions}


def correct_questions_node(state: WorkflowState) -> dict:
    """节点: OCR 纠错

    对标记了 needs_correction 的题目执行 OCR 纠错。
    未标记的题目直接通过，不消耗额外 LLM 调用。
    """
    console.print("[bold yellow]步骤 2.5: OCR 纠错检查[/bold yellow]")
    step_start = time.time()

    questions = state.get("questions", [])
    if not questions:
        logger.info("纠错跳过: 无题目")
        return {"questions": questions}

    # 筛选需要纠错的题目
    flagged = [q for q in questions if q.get("needs_correction", False)]

    if not flagged:
        logger.info("纠错跳过: 无需纠错的题目")
        console.print("[green]✓ 所有题目均无 OCR 错误标记，跳过纠错[/green]")
        return {"questions": questions}

    console.print(f"[cyan]发现 {len(flagged)} 道题目需要纠错（共 {len(questions)} 道）[/cyan]")
    logger.info(f"开始纠错: {len(flagged)}/{len(questions)} 道题目")

    # 加载原始 OCR 数据作为纠错上下文
    ocr_context = "{}"
    agent_input_path = os.path.join(RESULTS_DIR, "agent_input.json")
    if os.path.exists(agent_input_path):
        with open(agent_input_path, 'r', encoding='utf-8') as f:
            ocr_context = f.read()

    # 调用纠错工具
    from error_correction_agent.tools import correct_batch

    flagged_json = json.dumps(flagged, ensure_ascii=False)
    result_str = correct_batch.invoke({
        "questions_json": flagged_json,
        "ocr_context": ocr_context,
    })

    # 解析纠错结果
    try:
        corrected = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        logger.error(f"纠错结果解析失败: {result_str[:200]}")
        console.print("[red]⚠ 纠错结果解析失败，保留原始题目[/red]")
        return {"questions": questions}

    # 按 question_id 合并纠错结果
    corrected_map = {q["question_id"]: q for q in corrected}

    merged = []
    for q in questions:
        qid = q.get("question_id")
        if qid in corrected_map:
            cq = corrected_map[qid]
            corrections = cq.pop("corrections_applied", [])
            cq["needs_correction"] = False
            cq["ocr_issues"] = None
            merged.append(cq)
            logger.info(f"题目 {qid} 已纠错: {corrections}")
        else:
            merged.append(q)

    # 更新 questions.json
    questions_file = os.path.join(RESULTS_DIR, "questions.json")
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    logger.info(f"纠错完成: {len(corrected)}/{len(flagged)} 道题目已修复，耗时 {time.time() - step_start:.2f}s")
    console.print(f"[green]✓ 纠错完成: {len(corrected)} 道题目已修复[/green]")

    return {"questions": merged}


def export_node(state: WorkflowState) -> dict:
    """节点: 导出错题本"""
    console.print("[bold yellow]步骤 3: 导出错题本[/bold yellow]")
    step_start = time.time()
    output_path = export_wrongbook(state["questions"], state["selected_ids"])
    logger.info(f"导出完成: {output_path}，耗时 {time.time() - step_start:.2f}s")
    return {"output_path": output_path}


# ── 构建工作流图 ────────────────────────────────────────────


def build_workflow():
    """
    构建并编译工作流图。

    图结构:

        START → prepare_input → [中断] → split_questions → correct_questions → [中断] → export → END

    OCR 解析由 split_questions 内的 OCRMiddleware 中间件自动完成，
    不再需要独立的 ocr_parse 节点。
    纠错节点在分割后自动执行，仅对标记了 needs_correction 的题目调用纠错智能体。

    Returns:
        编译后的 CompiledStateGraph 实例
    """
    builder = StateGraph(WorkflowState)

    # 添加节点
    builder.add_node("prepare_input", prepare_input_node)
    builder.add_node("split_questions", split_questions_node)
    builder.add_node("correct_questions", correct_questions_node)
    builder.add_node("export", export_node)

    # 定义边
    builder.add_edge(START, "prepare_input")
    builder.add_edge("prepare_input", "split_questions")
    builder.add_edge("split_questions", "correct_questions")
    builder.add_edge("correct_questions", "export")
    builder.add_edge("export", END)

    # 编译：MemorySaver 保存中间状态，interrupt_before 在关键节点前暂停
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["split_questions", "export"],
    )

    return graph
