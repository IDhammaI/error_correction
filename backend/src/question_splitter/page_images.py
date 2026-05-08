"""Resolve per-page images that should be sent to Baidu paper_cut_edu."""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .coordinate_mapper import compute_coordinate_trust


def get_image_size(image_path: str) -> tuple[int, int] | tuple[None, None]:
    try:
        from PIL import Image

        with Image.open(image_path) as image:
            return image.size
    except Exception:
        return None, None


def _find_input_image_path(
    *,
    source_path: str,
    layout_index: int,
    output_dir: str,
) -> Optional[str]:
    source_stem = Path(source_path).stem
    candidates: List[str] = [
        os.path.join(output_dir, f"input_image_{source_stem}_{layout_index}.jpg")
    ]
    pattern = os.path.join(output_dir, f"input_image_{source_stem}_{layout_index}.*")
    candidates.extend(sorted(glob.glob(pattern)))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _source_result_pairs(
    raw_ocr_results: Iterable[Dict[str, Any]],
    source_paths: Iterable[str],
) -> List[Tuple[str, Dict[str, Any]]]:
    paths = list(source_paths or [])
    results = list(raw_ocr_results or [])
    return [
        (paths[idx] if idx < len(paths) else "", result)
        for idx, result in enumerate(results)
    ]


def extract_page_image_sources(
    raw_ocr_results: Iterable[Dict[str, Any]],
    source_paths: Iterable[str],
    *,
    output_dir: str,
    ocr_credentials: Optional[Dict[str, Any]] = None,
    baidu_enhance: bool = False,
) -> tuple[List[Dict[str, Any]], List[str]]:
    """Build page-indexed image metadata from PaddleOCR raw results."""

    page_sources: List[Dict[str, Any]] = []
    warnings: List[str] = []
    page_index = 0

    for source_path, result in _source_result_pairs(raw_ocr_results, source_paths):
        source_type = "pdf" if str(source_path).lower().endswith(".pdf") else "image"
        for layout_index, layout_page in enumerate(result.get("layoutParsingResults", []) or []):
            pruned = layout_page.get("prunedResult") or {}
            ocr_width = pruned.get("width")
            ocr_height = pruned.get("height")

            baidu_image_path = None
            if source_type == "image" and layout_index == 0 and source_path:
                baidu_image_path = source_path
            else:
                baidu_image_path = _find_input_image_path(
                    source_path=source_path,
                    layout_index=layout_index,
                    output_dir=output_dir,
                )

            baidu_width = None
            baidu_height = None
            if baidu_image_path:
                baidu_width, baidu_height = get_image_size(baidu_image_path)
            else:
                warnings.append(
                    f"BAIDU_PAPER_CUT_PAGE_IMAGE_MISSING: page_index={page_index}"
                )

            ocr_width = ocr_width or baidu_width
            ocr_height = ocr_height or baidu_height

            trust = compute_coordinate_trust(
                ocr_width=ocr_width,
                ocr_height=ocr_height,
                image_width=baidu_width,
                image_height=baidu_height,
                ocr_credentials=ocr_credentials,
                baidu_enhance=baidu_enhance,
            )

            page_sources.append(
                {
                    "page_index": page_index,
                    "source_file": source_path,
                    "source_type": source_type,
                    "layout_index": layout_index,
                    "ocr_page_width": ocr_width,
                    "ocr_page_height": ocr_height,
                    "baidu_image_path": baidu_image_path,
                    "baidu_image_width": baidu_width,
                    "baidu_image_height": baidu_height,
                    "coordinate_trust": trust,
                }
            )
            page_index += 1

    return page_sources, warnings


def discover_page_image_sources_from_ocr_data(
    ocr_data: Iterable[Dict[str, Any]],
    source_paths: Iterable[str],
    *,
    output_dir: str,
    ocr_credentials: Optional[Dict[str, Any]] = None,
    baidu_enhance: bool = False,
) -> tuple[List[Dict[str, Any]], List[str]]:
    """Best-effort page image discovery when only simplified OCR cache exists."""

    paths = list(source_paths or [])
    warnings: List[str] = []
    page_sources: List[Dict[str, Any]] = []
    pdf_paths = [p for p in paths if str(p).lower().endswith(".pdf")]
    image_paths = [p for p in paths if not str(p).lower().endswith(".pdf")]
    ocr_pages = list(ocr_data or [])
    pdf_page_count = max(0, len(ocr_pages) - len(image_paths)) if pdf_paths else 0
    pdf_rendered_pages: List[Tuple[str, str, int]] = []
    for pdf_path in pdf_paths:
        pattern = os.path.join(output_dir, f"input_image_{Path(pdf_path).stem}_*.jpg")
        for match in sorted(glob.glob(pattern)):
            try:
                layout_index = int(Path(match).stem.rsplit("_", 1)[-1])
            except ValueError:
                layout_index = 0
            pdf_rendered_pages.append((pdf_path, match, layout_index))

    image_cursor = 0
    pdf_cursor = 0
    for fallback_page_index, page in enumerate(ocr_pages):
        page_index = int(page.get("page_index", fallback_page_index))
        ocr_width = page.get("page_width")
        ocr_height = page.get("page_height")
        baidu_image_path = None
        source_file = ""
        source_type = "unknown"
        layout_index = page_index

        if page_index < pdf_page_count:
            source_type = "pdf"
            if pdf_cursor < len(pdf_rendered_pages):
                source_file, baidu_image_path, layout_index = pdf_rendered_pages[pdf_cursor]
            elif pdf_paths:
                source_file = pdf_paths[0]
            pdf_cursor += 1
        elif image_cursor < len(image_paths):
            source_file = image_paths[image_cursor]
            source_type = "image"
            baidu_image_path = source_file
            image_cursor += 1

        baidu_width = None
        baidu_height = None
        if baidu_image_path:
            baidu_width, baidu_height = get_image_size(baidu_image_path)
        else:
            warnings.append(
                f"BAIDU_PAPER_CUT_PAGE_IMAGE_MISSING: page_index={page_index}"
            )

        ocr_width = ocr_width or baidu_width
        ocr_height = ocr_height or baidu_height

        trust = compute_coordinate_trust(
            ocr_width=ocr_width,
            ocr_height=ocr_height,
            image_width=baidu_width,
            image_height=baidu_height,
            ocr_credentials=ocr_credentials,
            baidu_enhance=baidu_enhance,
        )
        page_sources.append(
            {
                "page_index": page_index,
                "source_file": source_file,
                "source_type": source_type,
                "layout_index": layout_index,
                "ocr_page_width": ocr_width,
                "ocr_page_height": ocr_height,
                "baidu_image_path": baidu_image_path,
                "baidu_image_width": baidu_width,
                "baidu_image_height": baidu_height,
                "coordinate_trust": trust,
            }
        )

    return page_sources, warnings
