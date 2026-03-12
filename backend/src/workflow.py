"""
错题本生成工作流 - LangGraph 实现
使用 StateGraph 将每个处理步骤定义为图节点
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, TypedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from rich.console import Console
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from config import settings
from .utils import prepare_input, export_wrongbook, simplify_ocr_results, run_async

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
    model_provider: str                  # 模型供应商: "openai" | "anthropic"


# ── 节点函数 ──────────────────────────────────────────────


def prepare_input_node(state: WorkflowState) -> dict:
    """节点: 准备输入（验证文件并复制到工作目录），支持多文件"""
    console.print("[bold yellow]步骤 1: 准备输入文件[/bold yellow]")
    step_start = time.time()

    file_paths = state["file_paths"]
    all_paths = []
    for fp in file_paths:
        all_paths.extend(prepare_input(fp))

    logger.info(f"步骤1完成: 准备输入文件，共 {len(all_paths)} 个文件（来自 {len(file_paths)} 个文件），耗时 {time.time() - step_start:.2f}s")
    return {"image_paths": all_paths}


# ── 并行分割辅助函数 ──────────────────────────────────────────


def _run_ocr_and_simplify(file_paths: List[str]) -> List[Dict[str, Any]]:
    """执行 OCR 解析并简化结果（含重试机制）

    支持混合文件类型：PDF 直传 API，图片并行上传。
    然后将结果简化为 split_batch 所需的格式。

    Returns:
        简化后的 OCR 数据列表，每项包含 page_index 和 blocks
    """
    from src.paddleocr_client import PaddleOCRClient

    client = PaddleOCRClient()

    # 按文件类型分组
    pdf_paths = [p for p in file_paths if p.lower().endswith(".pdf")]
    image_paths = [p for p in file_paths if not p.lower().endswith(".pdf")]

    max_retries = 3
    retry_delays = [15, 30, 60]
    ocr_results = []
    last_error = None

    # PDF 直传（每个 PDF 单独提交，API 内部处理分页）
    for pdf_path in pdf_paths:
        result = None
        for attempt in range(1, max_retries + 1):
            try:
                result = client.parse_pdf(pdf_path, save_output=True)
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = retry_delays[attempt - 1]
                    logger.warning(f"OCR PDF 第 {attempt} 次失败 ({e})，{delay}s 后重试...")
                    console.print(f"[yellow]OCR PDF 第 {attempt} 次失败，{delay}s 后重试...[/yellow]")
                    time.sleep(delay)
                else:
                    logger.error(f"OCR PDF 全部 {max_retries} 次重试失败: {last_error}")
                    console.print(f"[red]OCR PDF 解析失败（已重试 {max_retries} 次）: {last_error}[/red]")
        if result is not None:
            ocr_results.append(result)

    # 图片并行上传
    if image_paths:
        img_results = None
        for attempt in range(1, max_retries + 1):
            try:
                img_results = run_async(
                    client.parse_images_async(image_paths, save_output=True)
                )
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = retry_delays[attempt - 1]
                    logger.warning(f"OCR 图片第 {attempt} 次失败 ({e})，{delay}s 后重试...")
                    console.print(f"[yellow]OCR 图片第 {attempt} 次失败，{delay}s 后重试...[/yellow]")
                    time.sleep(delay)
                else:
                    logger.error(f"OCR 图片全部 {max_retries} 次重试失败: {last_error}")
                    console.print(f"[red]OCR 图片解析失败（已重试 {max_retries} 次）: {last_error}[/red]")
        if img_results:
            ocr_results.extend(img_results)

    if not ocr_results:
        return []

    return simplify_ocr_results(ocr_results)


def _build_overlapping_batches(
    ocr_data: List[Dict[str, Any]],
    batch_size: int = 2,
    overlap: int = 1,
) -> List[List[Dict[str, Any]]]:
    """构建重叠批次

    每批 batch_size 页，相邻批次重叠 overlap 页。
    例如 5 页, batch_size=2, overlap=1:
        批次0: [page0, page1]
        批次1: [page1, page2]
        批次2: [page2, page3]
        批次3: [page3, page4]
    """
    if not ocr_data:
        return []

    n_pages = len(ocr_data)
    if n_pages <= batch_size:
        return [ocr_data]

    step = batch_size - overlap
    batches = []
    for start in range(0, n_pages, step):
        end = min(start + batch_size, n_pages)
        batches.append(ocr_data[start:end])
        if end >= n_pages:
            break

    return batches


def _load_db_context():
    """加载数据库已有科目和标签"""
    db_subjects = []
    db_tags = []
    try:
        from db import SessionLocal
        from db.crud import get_existing_subjects, get_existing_tag_names

        with SessionLocal() as db:
            db_subjects = get_existing_subjects(db)
            db_tags = get_existing_tag_names(db)

        logger.info(f"已加载 DB 上下文: {len(db_subjects)} 个科目, {len(db_tags)} 个标签")
    except Exception as e:
        logger.warning(f"加载 DB 上下文失败（不影响分割）: {e}")
    return db_subjects, db_tags


def _extract_text_sample(ocr_data: List[Dict[str, Any]]) -> str:
    """从 OCR 数据前 2 页提取文本

    只读取 text / paragraph_title / doc_title 类型的 block。

    Args:
        ocr_data: 简化后的 OCR 数据列表

    Returns:
        拼接的文本字符串
    """
    if not ocr_data:
        return ""

    text_sample = ""
    for page in ocr_data[:2]:
        for block in page.get("blocks", []):
            if block.get("block_label") in ("text", "paragraph_title", "doc_title"):
                text_sample += block.get("block_content", "") + "\n"
    return text_sample


def _identify_subject(
    ocr_data: List[Dict[str, Any]],
    db_subjects: List[str],
    model_provider: str = "openai",
) -> str:
    """从 OCR 数据前几页识别科目（三层 fallback）

    1. LLM 预检（轻量模型，失败时静默 fallback）
    2. 关键词匹配（DB 已有科目 + 通用关键词）
    3. 内容特征推断（指标词计数）

    Args:
        ocr_data: 简化后的 OCR 数据列表
        db_subjects: 数据库已有科目列表
        model_provider: 模型供应商
    """
    if not ocr_data:
        return ""

    text_sample = _extract_text_sample(ocr_data)

    # ── 第 1 层：LLM 预检 ──
    try:
        from error_correction_agent.agent import detect_subject_via_llm

        llm_result = detect_subject_via_llm(text_sample, db_subjects, provider=model_provider)
        if llm_result:
            logger.info(f"LLM 科目识别成功: {llm_result}")
            return llm_result
    except Exception as e:
        logger.warning(f"LLM 科目识别失败，回退关键词匹配: {e}")

    # ── 第 2 层：关键词匹配 ──
    # 优先匹配 DB 已有科目
    for subj in db_subjects:
        if subj in text_sample:
            return subj

    # 通用关键词匹配
    subject_keywords = {
        "高中数学": ["数学试卷", "数学考试", "数学试题", "高中数学"],
        "高中物理": ["物理试卷", "物理考试", "物理试题", "高中物理"],
        "高中化学": ["化学试卷", "化学考试", "化学试题", "高中化学"],
        "高中生物": ["生物试卷", "生物考试", "生物试题", "高中生物"],
        "高中英语": ["英语试卷", "英语考试", "英语试题", "高中英语"],
        "高中语文": ["语文试卷", "语文考试", "语文试题", "高中语文"],
        "初中数学": ["初中数学"],
        "初中物理": ["初中物理"],
        "初中化学": ["初中化学"],
    }
    for subj, keywords in subject_keywords.items():
        for kw in keywords:
            if kw in text_sample:
                return subj

    # ── 第 3 层：内容特征推断 ──
    indicators = {
        "高中数学": ["函数", "方程", "不等式", "三角", "向量", "概率", "数列", "导数", "圆锥", "椭圆"],
        "高中物理": ["力", "速度", "加速度", "电场", "磁场", "动能", "势能"],
        "高中化学": ["离子", "溶液", "元素", "原子", "分子", "化学反应"],
    }
    scores = {subj: sum(1 for w in words if w in text_sample) for subj, words in indicators.items()}
    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best

    return ""


def _dedup_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 question_id 去重

    当多个批次产出相同 question_id 的题目时（因为重叠页），
    保留内容更丰富的版本（总文本更长）。
    """
    if not questions:
        return []

    seen: Dict[str, Dict[str, Any]] = {}
    for q in questions:
        qid = q.get("question_id", "")
        if not qid:
            continue
        if qid not in seen:
            seen[qid] = q
        else:
            # 保留内容更丰富的版本
            if _question_richness(q) > _question_richness(seen[qid]):
                seen[qid] = q

    result = list(seen.values())
    result.sort(key=lambda q: _sort_key(q.get("question_id", "")))
    return result


def _question_richness(q: Dict[str, Any]) -> int:
    """计算题目内容丰富度（总字符数）"""
    score = 0
    for block in q.get("content_blocks", []):
        score += len(block.get("content", ""))
    for opt in (q.get("options") or []):
        score += len(opt)
    return score


def _sort_key(qid: str):
    """题号排序: 纯数字按数值，否则按字符串"""
    try:
        return (0, int(qid), "")
    except ValueError:
        return (1, 0, qid)


def split_questions_node(state: WorkflowState) -> dict:
    """节点: 并行 OCR + 分割题目

    不再依赖编排智能体的顺序处理，而是直接执行：
    1. OCR 解析（PaddleOCR，图片级并行）
    2. 构建重叠批次（2页/批，1页重叠）
    3. 并行调用 split_batch（批次级并行，每批独立的内层 agent）
    4. 按 question_id 去重（重叠页产生的重复题目）
    5. 保存结果
    """
    console.print("[bold yellow]步骤 2: 并行 OCR + 分割题目[/bold yellow]")
    step_start = time.time()

    results_dir = settings.results_dir
    os.makedirs(results_dir, exist_ok=True)

    file_paths = state["image_paths"]
    model_provider = state.get("model_provider", "openai")

    # 清空旧的 questions.json 和 split_metadata.json
    questions_file = os.path.join(results_dir, "questions.json")
    if os.path.exists(questions_file):
        os.remove(questions_file)
    meta_path = os.path.join(results_dir, "split_metadata.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)

    # ── Step 1: OCR 解析 ──
    console.print(f"[cyan]OCR 解析 {len(file_paths)} 个文件...[/cyan]")
    ocr_start = time.time()

    ocr_data = _run_ocr_and_simplify(file_paths)

    if not ocr_data:
        logger.error("OCR 解析失败，无数据返回")
        console.print("[red]⚠ OCR 解析失败[/red]")
        return {"questions": []}

    # 保存 agent_input.json（供纠错节点使用）
    agent_input_path = os.path.join(results_dir, "agent_input.json")
    with open(agent_input_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=2)

    total_blocks = sum(len(p.get("blocks", [])) for p in ocr_data)
    ocr_elapsed = time.time() - ocr_start
    logger.info(f"OCR 完成: {len(ocr_data)} 页, {total_blocks} 个 block, 耗时 {ocr_elapsed:.2f}s")
    console.print(f"[green]✓ OCR 完成: {len(ocr_data)} 页, {total_blocks} 个 block ({ocr_elapsed:.1f}s)[/green]")

    # ── Step 2: 加载 DB 上下文 ──
    db_subjects, db_tags = _load_db_context()

    # ── Step 3: 识别科目 ──
    subject = _identify_subject(ocr_data, db_subjects, model_provider=model_provider)
    if subject:
        console.print(f"[cyan]识别科目: {subject}[/cyan]")
        logger.info(f"识别科目: {subject}")

    # ── Step 3.5: 按科目过滤知识点标签 ──
    if subject and db_tags:
        from db import SessionLocal
        from db.crud import get_existing_tag_names

        try:
            with SessionLocal() as db:
                db_tags = get_existing_tag_names(db, subject=subject)
            logger.info(f"按科目 '{subject}' 过滤后剩余 {len(db_tags)} 个标签")
        except Exception as e:
            logger.warning(f"按科目过滤标签失败，使用全量标签: {e}")

    # ── Step 4: 构建重叠批次 ──
    batches = _build_overlapping_batches(ocr_data, batch_size=2, overlap=1)
    console.print(f"[cyan]构建 {len(batches)} 个批次（2页/批, 1页重叠）[/cyan]")

    # ── Step 5: 并行分割 ──
    split_start = time.time()
    console.print(f"[cyan]并行分割 {len(batches)} 个批次...[/cyan]")

    from error_correction_agent.tools import split_batch

    existing_tags_str = ",".join(db_tags) if db_tags else ""
    max_workers = min(len(batches), 3)
    batch_results: List[List[Dict[str, Any]]] = [[] for _ in range(len(batches))]

    max_batch_retries = 2

    def _invoke_split(batch_idx: int, batch_data: list) -> None:
        """在线程中调用 split_batch 并存储结果（含重试）"""
        for attempt in range(1, max_batch_retries + 1):
            try:
                result_str = split_batch.invoke({
                    "ocr_data": json.dumps(batch_data, ensure_ascii=False),
                    "subject": subject,
                    "existing_tags": existing_tags_str,
                    "model_provider": model_provider,
                })
                # split_batch 内部捕获异常并返回 "分割失败: ..." 字符串，
                # 需要检测这种情况并触发重试
                if not result_str or not result_str.startswith("["):
                    raise RuntimeError(f"split_batch 返回非JSON: {result_str[:200]}")
                questions = json.loads(result_str)
                batch_results[batch_idx] = questions
                logger.info(f"批次 {batch_idx} 完成: {len(questions)} 道题目")
                console.print(f"[green]  ✓ 批次 {batch_idx} 完成: {len(questions)} 道题目[/green]")
                return
            except Exception as e:
                if attempt < max_batch_retries:
                    logger.warning(f"批次 {batch_idx} 第 {attempt} 次失败 ({e})，重试中...")
                    console.print(f"[yellow]  ⚠ 批次 {batch_idx} 第 {attempt} 次失败，重试...[/yellow]")
                    time.sleep(2)
                else:
                    logger.error(f"批次 {batch_idx} 分割失败（已重试 {max_batch_retries} 次）: {e}")
                    console.print(f"[red]  ✗ 批次 {batch_idx} 失败: {e}[/red]")

    if len(batches) == 1:
        _invoke_split(0, batches[0])
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_invoke_split, i, batch): i
                for i, batch in enumerate(batches)
            }
            # 等待全部完成
            for future in as_completed(futures):
                future.result()  # 触发异常传播（已在 _invoke_split 内处理）

    split_elapsed = time.time() - split_start
    logger.info(f"并行分割完成, 耗时 {split_elapsed:.2f}s")

    # ── Step 6: 合并 + 去重 ──
    all_questions = []
    for questions in batch_results:
        all_questions.extend(questions)

    before_dedup = len(all_questions)
    deduped = _dedup_questions(all_questions)
    after_dedup = len(deduped)

    if before_dedup > after_dedup:
        logger.info(f"去重: {before_dedup} → {after_dedup} 道题目（移除 {before_dedup - after_dedup} 道重复）")
        console.print(f"[yellow]去重: 移除 {before_dedup - after_dedup} 道重复题目[/yellow]")

    # ── Step 7: 保存结果 ──
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    if subject:
        meta = {"subject": subject}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    total_elapsed = time.time() - step_start
    if deduped:
        logger.info(f"分割完成: 共 {len(deduped)} 道题目, 总耗时 {total_elapsed:.2f}s")
        console.print(f"[bold green]✓ 成功分割 {len(deduped)} 道题目 (总耗时 {total_elapsed:.1f}s)[/bold green]")
    else:
        logger.warning("未生成任何题目，请检查执行日志")
        console.print("[yellow]⚠ 未生成任何题目[/yellow]")

    return {"questions": deduped}


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
    agent_input_path = os.path.join(settings.results_dir, "agent_input.json")
    if os.path.exists(agent_input_path):
        with open(agent_input_path, 'r', encoding='utf-8') as f:
            ocr_context = f.read()

    # 调用纠错工具
    from error_correction_agent.tools import correct_batch

    model_provider = state.get("model_provider", "openai")
    flagged_json = json.dumps(flagged, ensure_ascii=False)
    result_str = correct_batch.invoke({
        "questions_json": flagged_json,
        "ocr_context": ocr_context,
        "model_provider": model_provider,
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
    questions_file = os.path.join(settings.results_dir, "questions.json")
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

    split_questions 节点直接执行 OCR + 并行分割（不再依赖编排智能体）:
    1. 调用 PaddleOCR API 解析图片（图片级并行）
    2. 构建重叠批次 → 并行调用 split_batch（批次级并行）
    3. 按 question_id 去重 → 保存结果

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
