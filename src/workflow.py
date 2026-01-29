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

from .paddleocr_client import PaddleOCRClient
from .utils import prepare_input, export_wrongbook

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
    file_path: str                       # 输入文件路径
    image_paths: List[str]               # 标准化后的图片路径列表
    ocr_results: List[Dict[str, Any]]    # OCR 解析结果
    questions: List[Dict[str, Any]]      # 分割后的题目列表
    selected_ids: List[str]              # 用户选中的题目 ID
    output_path: str                     # 导出文件路径


# ── 节点函数 ──────────────────────────────────────────────


def prepare_input_node(state: WorkflowState) -> dict:
    """节点: 准备输入（PDF/图片 → 标准化图片列表）"""
    console.print("[bold yellow]步骤 1: 准备输入文件[/bold yellow]")
    step_start = time.time()
    image_paths = prepare_input(state["file_path"])
    logger.info(f"步骤1完成: 准备输入文件，共 {len(image_paths)} 张图片，耗时 {time.time() - step_start:.2f}s")
    return {"image_paths": image_paths}


def ocr_parse_node(state: WorkflowState) -> dict:
    """节点: PaddleOCR 解析"""
    console.print("[bold yellow]步骤 2: PaddleOCR 解析[/bold yellow]")
    step_start = time.time()
    client = PaddleOCRClient()
    results = []
    for image_path in state["image_paths"]:
        result = client.parse_image(image_path, save_output=True)
        results.append(result)
    logger.info(f"步骤2完成: OCR解析，共 {len(results)} 个结果，耗时 {time.time() - step_start:.2f}s")
    console.print(f"[green]✓ 成功解析 {len(results)} 张图片[/green]")
    return {"ocr_results": results}


def split_questions_node(state: WorkflowState) -> dict:
    """节点: Agent 智能分割题目"""
    console.print("[bold yellow]步骤 3: Agent 分割题目[/bold yellow]")
    step_start = time.time()

    # 清除上一次的结果文件，避免 Agent 失败时读到旧数据
    results_dir = os.getenv("RESULTS_DIR", "results")
    questions_file = os.path.join(results_dir, "questions.json")
    if os.path.exists(questions_file):
        os.remove(questions_file)

    from error_correction_agent.agent import create_question_split_agent

    logger.info("开始调用Agent分割题目")
    agent = create_question_split_agent()

    # 简化 OCR 结果为 Agent 友好格式
    simplified_results = []
    for result in state["ocr_results"]:
        if "layoutParsingResults" in result:
            for page in result["layoutParsingResults"]:
                if "prunedResult" in page:
                    parsing_res = page["prunedResult"].get("parsing_res_list", [])
                    simplified_results.append({
                        "blocks": parsing_res,
                        "block_order": page.get("block_order", [])
                    })

    prompt = f"""请分析以下OCR识别结果，将其分割为独立的题目。

OCR结果包含 {len(simplified_results)} 页内容。

每页的数据结构：
- blocks: 包含所有识别的内容块（文本、公式、图片等）
- block_order: 推荐的阅读顺序

请仔细分析题号、内容结构，将题目准确分割，并使用 save_questions 工具保存结果。

如果遇到不确定的情况，请使用 log_issue 工具记录。
"""

    console.print(f"[cyan]Agent 输入: {len(simplified_results)} 页, 共 {sum(len(r.get('blocks', [])) for r in simplified_results)} 个 block[/cyan]")

    response = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "user", "content": f"OCR数据: {simplified_results}"}
            ]
        },
        config={"recursion_limit": 50},
    )

    # 打印 Agent 响应摘要，便于排查
    if response and "messages" in response:
        for msg in response["messages"]:
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")
            if role != "human":
                preview = str(content)[:200] if content else "(empty)"
                console.print(f"[dim]  [{role}] {preview}[/dim]")

    # 从文件读取 Agent 保存的结果（路径已在函数开头定义）
    questions = []
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        logger.info(f"Agent分割完成: 共 {len(questions)} 道题目，耗时 {time.time() - step_start:.2f}s")
        console.print(f"[green]✓ 成功加载 {len(questions)} 道题目[/green]")
    else:
        logger.warning("Agent未保存题目，请检查执行日志")
        console.print("[yellow]⚠ Agent未保存题目，请检查执行日志[/yellow]")
        console.print("[yellow]  可能原因: Agent 未调用 save_questions 工具，或工具调用失败[/yellow]")

    return {"questions": questions}


def export_node(state: WorkflowState) -> dict:
    """节点: 导出错题本"""
    console.print("[bold yellow]步骤 4: 导出错题本[/bold yellow]")
    step_start = time.time()
    output_path = export_wrongbook(state["questions"], state["selected_ids"])
    logger.info(f"导出完成: {output_path}，耗时 {time.time() - step_start:.2f}s")
    return {"output_path": output_path}


# ── 构建工作流图 ────────────────────────────────────────────


def build_workflow():
    """
    构建并编译工作流图。

    图结构:

        START → prepare_input → ocr_parse → [中断] → split_questions → [中断] → export → END

    在 split_questions 和 export 节点前设置中断，
    以支持 Web 端的分步交互（上传 → 分割 → 导出）。

    Returns:
        编译后的 CompiledStateGraph 实例
    """
    builder = StateGraph(WorkflowState)

    # 添加节点
    builder.add_node("prepare_input", prepare_input_node)
    builder.add_node("ocr_parse", ocr_parse_node)
    builder.add_node("split_questions", split_questions_node)
    builder.add_node("export", export_node)

    # 定义边
    builder.add_edge(START, "prepare_input")
    builder.add_edge("prepare_input", "ocr_parse")
    builder.add_edge("ocr_parse", "split_questions")
    builder.add_edge("split_questions", "export")
    builder.add_edge("export", END)

    # 编译：MemorySaver 保存中间状态，interrupt_before 在关键节点前暂停
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["split_questions", "export"],
    )

    return graph
