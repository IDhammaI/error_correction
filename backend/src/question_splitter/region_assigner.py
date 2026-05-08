"""Map PaddleOCR blocks to Baidu paper_cut_edu question regions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .models import BBox, OcrBlock, QuestionRegion
from .ocr_blocks import bbox_from_points, normalize_bbox


def bbox_area(bbox: BBox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def bbox_intersection(a: BBox, b: BBox) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def center_inside(inner: BBox, outer: BBox) -> bool:
    cx = (inner[0] + inner[2]) / 2
    cy = (inner[1] + inner[3]) / 2
    return outer[0] <= cx <= outer[2] and outer[1] <= cy <= outer[3]


def y_overlap_ratio(a: BBox, b: BBox) -> float:
    top = max(a[1], b[1])
    bottom = min(a[3], b[3])
    height = max(1.0, min(a[3] - a[1], b[3] - b[1]))
    return max(0.0, bottom - top) / height


def region_score(block_bbox: BBox, region_bbox: BBox) -> float:
    block_area = max(1.0, bbox_area(block_bbox))
    region_area = max(1.0, bbox_area(region_bbox))
    overlap = bbox_intersection(block_bbox, region_bbox)
    overlap_over_block = overlap / block_area
    overlap_over_region = overlap / region_area
    center_bonus = 0.35 if center_inside(block_bbox, region_bbox) else 0.0
    return overlap_over_block + 0.25 * overlap_over_region + 0.2 * y_overlap_ratio(block_bbox, region_bbox) + center_bonus


def _region_bbox(question: Dict[str, Any]) -> Optional[BBox]:
    normalized = normalize_bbox(question.get("normalized_bbox"))
    if normalized:
        return normalized

    location = question.get("qus_location") or question.get("location") or {}
    if isinstance(location, dict):
        bbox = normalize_bbox(location.get("bbox"))
        if bbox:
            return bbox
        return bbox_from_points(location.get("points"))
    return normalize_bbox(location)


def parse_baidu_regions(page_results: Iterable[Dict[str, Any]]) -> List[QuestionRegion]:
    regions: List[QuestionRegion] = []
    for page in page_results or []:
        page_index = int(page.get("page_index", 0))
        raw_result = page.get("result") or {}
        questions = raw_result.get("qus_result") or []
        for region_index, question in enumerate(questions):
            bbox = _region_bbox(question)
            if not bbox:
                continue
            location = question.get("qus_location") or {}
            polygon = location.get("points") if isinstance(location, dict) else None
            regions.append(
                QuestionRegion(
                    page_index=page_index,
                    region_index=region_index,
                    bbox=bbox,
                    polygon=polygon if isinstance(polygon, list) else None,
                    raw=question,
                )
            )
    return sorted(regions, key=lambda item: (item.page_index, item.bbox[1], item.bbox[0]))


def assign_region(
    block: OcrBlock,
    regions: Iterable[QuestionRegion],
    *,
    min_score: float = 0.15,
) -> Optional[QuestionRegion]:
    if not block.bbox:
        return None
    best: Optional[QuestionRegion] = None
    best_score = 0.0
    for region in regions:
        if region.page_index != block.page_index:
            continue
        score = region_score(block.bbox, region.bbox)
        if score > best_score:
            best = region
            best_score = score
    if best and best_score >= min_score:
        return best
    return None
