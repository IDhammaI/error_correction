"""Coordinate normalization between PaddleOCR blocks and Baidu regions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .models import BBox
from .ocr_blocks import bbox_from_points, normalize_bbox


TRUST_HIGH = "high"
TRUST_MEDIUM = "medium"
TRUST_LOW = "low"


def normalize_bbox_to_page(
    bbox: BBox | List[float] | Tuple[float, float, float, float] | None,
    width: Any,
    height: Any,
) -> Optional[BBox]:
    raw = normalize_bbox(bbox)
    if not raw:
        return None
    try:
        w = float(width)
        h = float(height)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return (
        max(0.0, min(1.0, raw[0] / w)),
        max(0.0, min(1.0, raw[1] / h)),
        max(0.0, min(1.0, raw[2] / w)),
        max(0.0, min(1.0, raw[3] / h)),
    )


def compute_coordinate_trust(
    *,
    ocr_width: Any,
    ocr_height: Any,
    image_width: Any,
    image_height: Any,
    ocr_credentials: Optional[Dict[str, Any]] = None,
    baidu_enhance: bool = False,
) -> str:
    try:
        ow = float(ocr_width)
        oh = float(ocr_height)
        iw = float(image_width)
        ih = float(image_height)
    except (TypeError, ValueError):
        return TRUST_LOW
    if min(ow, oh, iw, ih) <= 0:
        return TRUST_LOW

    aspect_ocr = ow / oh
    aspect_baidu = iw / ih
    aspect_diff = abs(aspect_ocr - aspect_baidu) / max(aspect_ocr, aspect_baidu)

    creds = ocr_credentials or {}
    geometry_changed = bool(
        creds.get("use_doc_orientation")
        or creds.get("use_doc_unwarping")
        or baidu_enhance
    )

    if aspect_diff <= 0.03 and not geometry_changed:
        return TRUST_HIGH
    if aspect_diff <= 0.10:
        return TRUST_MEDIUM
    return TRUST_LOW


def _baidu_region_bbox(question: Dict[str, Any]) -> Optional[BBox]:
    location = question.get("qus_location") or question.get("location") or {}
    if isinstance(location, dict):
        bbox = normalize_bbox(location.get("bbox"))
        if bbox:
            return bbox
        return bbox_from_points(location.get("points"))
    return normalize_bbox(location)


def apply_coordinate_mapping(
    ocr_data: Iterable[Dict[str, Any]],
    baidu_page_results: Iterable[Dict[str, Any]],
    page_image_sources: Iterable[Dict[str, Any]] | None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Return copies with normalized bboxes attached.

    The splitter and assigner consume normalized bbox fields when present, so
    OCR and Baidu coordinates can be compared even when their raw resolutions
    differ.
    """

    source_by_page = {
        int(item.get("page_index")): item
        for item in (page_image_sources or [])
        if item.get("page_index") is not None
    }

    mapped_ocr: List[Dict[str, Any]] = []
    coordinate_pages: List[Dict[str, Any]] = []
    for fallback_page_index, page in enumerate(ocr_data or []):
        page_copy = deepcopy(page)
        page_index = int(page_copy.get("page_index", fallback_page_index))
        source = source_by_page.get(page_index, {})
        ocr_width = source.get("ocr_page_width") or page_copy.get("page_width")
        ocr_height = source.get("ocr_page_height") or page_copy.get("page_height")
        trust = source.get("coordinate_trust") or TRUST_LOW

        for block in page_copy.get("blocks", []) or []:
            norm = normalize_bbox_to_page(
                block.get("block_bbox"),
                ocr_width,
                ocr_height,
            )
            if norm:
                block["normalized_bbox"] = list(norm)
            block["coordinate_trust"] = trust

        coordinate_pages.append(
            {
                "page_index": page_index,
                "ocr_page_width": ocr_width,
                "ocr_page_height": ocr_height,
                "baidu_image_width": source.get("baidu_image_width"),
                "baidu_image_height": source.get("baidu_image_height"),
                "coordinate_trust": trust,
                "baidu_image_path": source.get("baidu_image_path"),
            }
        )
        mapped_ocr.append(page_copy)

    mapped_baidu: List[Dict[str, Any]] = []
    for page in baidu_page_results or []:
        page_copy = deepcopy(page)
        page_index = int(page_copy.get("page_index", 0))
        source = source_by_page.get(page_index, {})
        image_width = source.get("baidu_image_width")
        image_height = source.get("baidu_image_height")
        trust = source.get("coordinate_trust") or TRUST_LOW

        result = page_copy.get("result") or {}
        questions = result.get("qus_result") or []
        for question in questions:
            bbox = _baidu_region_bbox(question)
            norm = normalize_bbox_to_page(bbox, image_width, image_height)
            if norm:
                question["normalized_bbox"] = list(norm)
            question["coordinate_trust"] = trust

        mapped_baidu.append(page_copy)

    return mapped_ocr, mapped_baidu, {"pages": coordinate_pages}
