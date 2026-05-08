"""Build question objects from PaddleOCR blocks and Baidu split regions."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .coordinate_mapper import TRUST_LOW, apply_coordinate_mapping
from .models import OcrBlock, QuestionDraft, SplitSegment
from .ocr_blocks import extract_ocr_blocks, is_visual_label
from .region_assigner import assign_region, parse_baidu_regions


MAIN_QUESTION_RE = re.compile(r"(?m)(^|\n)\s*(?:第\s*(\d{1,3})\s*题|(\d{1,3})[\.．、])\s*")
SECONDARY_QUESTION_RE = re.compile(r"^\s*[（(](\d{1,3})[)）]\s*")
OPTION_LINE_RE = re.compile(r"^\s*[A-DＡ-Ｄ][\.．、]\s*")
SECTION_RE = re.compile(r"^\s*[一二三四五六七八九十]+[、.．]\s*")


def _question_type_from_text(text: str, fallback: str = "解答题") -> str:
    if any(key in text for key in ("选择", "单选", "多选")):
        return "选择题"
    if "填空" in text:
        return "填空题"
    if "判断" in text:
        return "判断题"
    if any(key in text for key in ("解答", "计算", "证明", "实验", "探究", "应用")):
        return "解答题"
    return fallback


def _looks_like_section(block: OcrBlock) -> bool:
    text = block.content.strip()
    if not text:
        return False
    if MAIN_QUESTION_RE.match(text):
        return False
    if block.label == "paragraph_title":
        return True
    if SECTION_RE.match(text) and any(
        key in text
        for key in ("选择", "填空", "判断", "解答", "计算", "实验", "探究", "应用", "题")
    ):
        return True
    return False


def _split_text_block(block: OcrBlock) -> List[SplitSegment]:
    text = block.content.strip()
    if not text:
        return []

    matches = list(MAIN_QUESTION_RE.finditer(text))
    if not matches:
        secondary = SECONDARY_QUESTION_RE.match(text)
        return [
            SplitSegment(
                page_index=block.page_index,
                order=block.order,
                label=block.label,
                content=text,
                bbox=block.bbox,
                raw=block.raw,
                starts_question=False,
                question_id=secondary.group(1) if secondary else None,
            )
        ]

    segments: List[SplitSegment] = []
    if matches[0].start() > 0:
        prefix = text[: matches[0].start()].strip()
        if prefix:
            segments.append(
                SplitSegment(
                    page_index=block.page_index,
                    order=block.order - 0.01,
                    label=block.label,
                    content=prefix,
                    bbox=block.bbox,
                    raw=block.raw,
                )
            )

    for idx, match in enumerate(matches):
        start = match.start(0)
        end = matches[idx + 1].start(0) if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        question_id = match.group(2) or match.group(3)
        segments.append(
            SplitSegment(
                page_index=block.page_index,
                order=block.order + idx / 100,
                label=block.label,
                content=content,
                bbox=block.bbox,
                raw=block.raw,
                starts_question=True,
                question_id=question_id,
            )
        )
    return segments


def _block_to_segments(block: OcrBlock) -> List[SplitSegment]:
    if is_visual_label(block.label):
        return [
            SplitSegment(
                page_index=block.page_index,
                order=block.order,
                label=block.label,
                content=block.content,
                bbox=block.bbox,
                raw=block.raw,
            )
        ]
    return _split_text_block(block)


def _extract_option_lines(text: str) -> Tuple[str, List[str]]:
    keep_lines: List[str] = []
    options: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if OPTION_LINE_RE.match(stripped):
            options.append(stripped)
        else:
            keep_lines.append(line)
    return "\n".join(keep_lines).strip(), options


def _draft_text(draft: QuestionDraft) -> str:
    return "\n".join(
        block.get("content", "")
        for block in draft.content_blocks
        if block.get("block_type") == "text"
    )


def _new_question_id(index: int) -> str:
    return str(index)


def _finalize_draft(draft: QuestionDraft) -> Dict[str, Any]:
    text = _draft_text(draft)
    if draft.options:
        draft.question_type = "选择题"
    else:
        draft.question_type = _question_type_from_text(text, draft.question_type)
    return {
        "section_title": draft.section_title,
        "question_id": draft.question_id,
        "question_type": draft.question_type,
        "content_blocks": draft.content_blocks,
        "options": draft.options,
        "answer": None,
        "analysis": None,
        "knowledge_tags": [],
        "needs_correction": True,
        "ocr_issues": ["API切题后保留 PaddleOCR 原文，需纠错智能体复核。"],
        "image_refs": draft.image_refs,
        "has_formula": draft.has_formula or "$" in text or "\\" in text,
        "has_image": draft.has_image,
        "source_pages": sorted(draft.page_indices),
        "source_regions": [
            {"page_index": page_index, "region_index": region_index}
            for page_index, region_index in draft.region_keys
        ],
    }


def build_questions_from_ocr(
    ocr_data: Iterable[Dict[str, Any]],
    baidu_page_results: Iterable[Dict[str, Any]] | None = None,
    *,
    subject: Optional[str] = None,
    page_image_sources: Iterable[Dict[str, Any]] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """Split PaddleOCR blocks into questions.

    Baidu regions are used as strong layout anchors, while PaddleOCR remains the
    source of text, formulas, and image references.
    """

    coordinate_mapping_enabled = page_image_sources is not None
    mapped_ocr, mapped_baidu, coordinate_debug = apply_coordinate_mapping(
        ocr_data,
        baidu_page_results or [],
        page_image_sources,
    )
    blocks = extract_ocr_blocks(mapped_ocr)
    regions = parse_baidu_regions(mapped_baidu)
    regions_by_page = defaultdict(list)
    for region in regions:
        regions_by_page[region.page_index].append(region)

    warnings: List[str] = []
    debug_assignments: List[Dict[str, Any]] = []
    current_section: Optional[str] = None
    current_question_type = "解答题"
    drafts: List[QuestionDraft] = []
    current: Optional[QuestionDraft] = None

    def start_draft(question_id: Optional[str], segment: SplitSegment) -> QuestionDraft:
        nonlocal current
        qid = question_id or _new_question_id(len(drafts) + 1)
        draft = QuestionDraft(
            question_id=qid,
            section_title=current_section,
            question_type=current_question_type,
        )
        drafts.append(draft)
        current = draft
        draft.add_segment(segment)
        return draft

    for block in blocks:
        if _looks_like_section(block):
            current_section = block.content.strip()
            current_question_type = _question_type_from_text(current_section, "解答题")
            continue

        coordinate_trust = block.raw.get("coordinate_trust")
        assigned = None
        if not coordinate_mapping_enabled or coordinate_trust != TRUST_LOW:
            assigned = assign_region(block, regions_by_page.get(block.page_index, []))
        region_key = (
            (assigned.page_index, assigned.region_index)
            if assigned is not None
            else None
        )
        debug_assignments.append(
            {
                "page_index": block.page_index,
                "block_order": block.order,
                "block_label": block.label,
                "coordinate_trust": coordinate_trust,
                "region_key": list(region_key) if region_key else None,
            }
        )

        for segment in _block_to_segments(block):
            segment.region_key = region_key

            content, options = _extract_option_lines(segment.content)
            if content != segment.content:
                segment.content = content

            should_start = segment.starts_question
            if not should_start and current is None and segment.question_id:
                should_start = True
            if (
                not should_start
                and current is not None
                and segment.region_key
                and current.region_keys
                and segment.region_key not in current.region_keys
                and content
            ):
                should_start = True

            if should_start:
                draft = start_draft(segment.question_id, segment)
            elif current is not None:
                draft = current
                draft.add_segment(segment)
            else:
                draft = start_draft(segment.question_id, segment)

            if options:
                draft.options.extend(option for option in options if option not in draft.options)

    questions = [
        _finalize_draft(draft)
        for draft in drafts
        if draft.content_blocks or draft.options or draft.image_refs
    ]

    if not regions:
        warnings.append("BAIDU_PAPER_CUT_NO_REGIONS: API未返回题目框，已仅按OCR题号和版面顺序切分。")
    if not questions and blocks:
        warnings.append("QUESTION_SPLIT_EMPTY: OCR有内容但未形成题目，请检查题号识别或API切题结果。")

    debug = {
        "subject": subject,
        "block_count": len(blocks),
        "region_count": len(regions),
        "question_count": len(questions),
        "coordinate_mapping": coordinate_debug,
        "assignments": debug_assignments,
    }
    return questions, debug, warnings
