"""Helpers for normalizing PaddleOCR blocks into splitter-friendly records."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .models import BBox, OcrBlock


TEXT_LABELS = {"text", "paragraph_title", "doc_title", "header", "formula"}
VISUAL_LABELS = {"image", "chart"}
NOISE_LABELS = {"footer", "page_number", "seal"}


def bbox_from_points(points: Any) -> Optional[BBox]:
    if not isinstance(points, list) or not points:
        return None
    xs: List[float] = []
    ys: List[float] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        try:
            xs.append(float(point["x"]))
            ys.append(float(point["y"]))
        except (KeyError, TypeError, ValueError):
            continue
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def normalize_bbox(value: Any) -> Optional[BBox]:
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            x1, y1, x2, y2 = [float(v) for v in value]
        except (TypeError, ValueError):
            return None
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        return x1, y1, x2, y2
    return bbox_from_points(value)


def is_text_label(label: str) -> bool:
    return label in TEXT_LABELS


def is_visual_label(label: str) -> bool:
    return label in VISUAL_LABELS


def is_noise_label(label: str) -> bool:
    return label in NOISE_LABELS


def extract_ocr_blocks(ocr_data: Iterable[Dict[str, Any]]) -> List[OcrBlock]:
    blocks: List[OcrBlock] = []
    for page_fallback_index, page in enumerate(ocr_data or []):
        page_index = int(page.get("page_index", page_fallback_index))
        for block_fallback_index, block in enumerate(page.get("blocks", []) or []):
            label = str(block.get("block_label") or "")
            if is_noise_label(label):
                continue
            content = block.get("block_content") or ""
            if not isinstance(content, str):
                content = str(content)

            raw_order = block.get("block_order")
            bbox = normalize_bbox(block.get("normalized_bbox")) or normalize_bbox(block.get("block_bbox"))
            try:
                order = float(raw_order)
            except (TypeError, ValueError):
                if bbox:
                    order = bbox[1] * 100000 + bbox[0]
                else:
                    order = float(block_fallback_index)

            polygon = block.get("block_polygon_points")
            blocks.append(
                OcrBlock(
                    page_index=page_index,
                    order=order,
                    label=label,
                    content=content.strip(),
                    bbox=bbox,
                    polygon=polygon if isinstance(polygon, list) else None,
                    block_id=block.get("block_id"),
                    group_id=block.get("group_id"),
                    raw=block,
                )
            )
    return sorted_blocks(blocks)


def sorted_blocks(blocks: Iterable[OcrBlock]) -> List[OcrBlock]:
    return sorted(
        blocks,
        key=lambda block: (
            block.page_index,
            block.order,
            block.bbox[1] if block.bbox else 0,
            block.bbox[0] if block.bbox else 0,
        ),
    )
