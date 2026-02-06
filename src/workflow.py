"""
错题本生成工作流 - LangGraph 实现
使用 StateGraph 将每个处理步骤定义为图节点
"""

import os
import json
import logging
import time
import asyncio
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
    file_paths: List[str]                # 输入文件路径列表（支持多文件）
    image_paths: List[str]               # 标准化后的图片路径列表
    ocr_results: List[Dict[str, Any]]    # OCR 解析结果
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


def _run_async(coro):
    """安全地运行异步协程，兼容已有事件循环的场景（如 LangGraph 内部）"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 已有事件循环在运行，无法直接 asyncio.run()
        # 在新线程中创建独立事件循环来执行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def ocr_parse_node(state: WorkflowState) -> dict:
    """节点: PaddleOCR 解析（异步并发）"""
    console.print("[bold yellow]步骤 2: PaddleOCR 解析[/bold yellow]")
    step_start = time.time()
    client = PaddleOCRClient()
    image_paths = state["image_paths"]

    # 使用异步并发解析所有图片（兼容已有事件循环）
    results = _run_async(client.parse_images_async(image_paths, save_output=True))

    logger.info(f"步骤2完成: OCR解析，共 {len(results)} 个结果，耗时 {time.time() - step_start:.2f}s")
    console.print(f"[green]✓ 成功解析 {len(results)} 张图片[/green]")
    return {"ocr_results": results}


def split_questions_node(state: WorkflowState) -> dict:
    """节点: Agent 智能分割题目"""
    console.print("[bold yellow]步骤 3: Agent 分割题目[/bold yellow]")
    step_start = time.time()

    results_dir = os.getenv("RESULTS_DIR", "results")
    os.makedirs(results_dir, exist_ok=True)

    from error_correction_agent.agent import create_split_agent

    logger.info("开始调用Agent分割题目")
    agent = create_split_agent()

    # 简化 OCR 结果：只保留 Agent 分割题目所需的字段
    simplified_results = []
    page_index = 0
    for result in state["ocr_results"]:
        if "layoutParsingResults" in result:
            for page in result["layoutParsingResults"]:
                if "prunedResult" in page:
                    parsing_res = page["prunedResult"].get("parsing_res_list", [])
                    slim_blocks = []
                    for b in parsing_res:
                        content = b.get("block_content", "")
                        # 图片 block 的 content 始终为空，用 bbox 构造实际图片路径
                        if b.get("block_label") == "image" and not content:
                            bbox = b.get("block_bbox")
                            if bbox:
                                content = f"/images/img_in_image_box_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}.jpg"
                        slim_blocks.append({
                            "block_label": b.get("block_label"),
                            "block_content": content,
                            "block_order": b.get("block_order"),
                        })
                    simplified_results.append({
                        "page_index": page_index,
                        "blocks": slim_blocks,
                    })
                    page_index += 1

    # 保存发送给 Agent 的 JSON 到本地
    agent_input_path = os.path.join(results_dir, "agent_input.json")
    with open(agent_input_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_results, f, ensure_ascii=False, indent=2)
    logger.info(f"Agent 输入数据已保存到: {agent_input_path}")

    prompt = f"""请分析以下OCR识别结果，将其分割为独立的题目。

OCR结果包含 {len(simplified_results)} 页内容，请严格按照 page_index 从小到大的顺序处理。

每页的数据结构：
- page_index: 页码索引（从0开始），决定全局阅读顺序
- blocks: 包含所有识别的内容块，每个 block 有三个字段：
  - block_label: 类型（text / image / doc_title / paragraph_title 等）
  - block_content: 文本内容（公式用 LaTeX 标记）或图片路径
  - block_order: 该 block 在页内的阅读顺序

请按 page_index 顺序处理每一页，再在每页内部按 block_order 顺序处理各 block，仔细分析题号、内容结构，将题目准确分割，返回结构化的题目列表。
"""

    console.print(f"[cyan]Agent 输入: {len(simplified_results)} 页, 共 {sum(len(r.get('blocks', [])) for r in simplified_results)} 个 block[/cyan]")

    response = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "user", "content": f"OCR数据: {simplified_results}"}
            ]
        },
        config={"recursion_limit": 300},
    )

    # 从 structured_response 获取结构化结果
    questions = []
    structured = response.get("structured_response")
    if structured is not None:
        # Pydantic 模型 → dict 列表
        questions = [q.model_dump() for q in structured.questions]

        # 保存到文件供后续步骤和前端使用
        questions_file = os.path.join(results_dir, "questions.json")
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

        logger.info(f"Agent分割完成: 共 {len(questions)} 道题目，耗时 {time.time() - step_start:.2f}s")
        console.print(f"[green]✓ 成功分割 {len(questions)} 道题目[/green]")
    else:
        logger.warning("Agent未返回结构化结果，请检查执行日志")
        console.print("[yellow]⚠ Agent未返回结构化结果[/yellow]")

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
