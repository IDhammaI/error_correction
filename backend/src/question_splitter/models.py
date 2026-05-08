"""Data models used by the API-backed question splitter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


BBox = Tuple[float, float, float, float]


@dataclass(frozen=True)
class OcrBlock:
    page_index: int
    order: float
    label: str
    content: str
    bbox: Optional[BBox] = None
    polygon: Optional[List[Dict[str, float]]] = None
    block_id: Optional[str] = None
    group_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QuestionRegion:
    page_index: int
    region_index: int
    bbox: BBox
    polygon: Optional[List[Dict[str, float]]] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SplitSegment:
    page_index: int
    order: float
    label: str
    content: str
    bbox: Optional[BBox]
    raw: Dict[str, Any]
    starts_question: bool = False
    question_id: Optional[str] = None
    region_key: Optional[tuple[int, int]] = None


@dataclass
class QuestionDraft:
    question_id: str
    section_title: Optional[str]
    question_type: str
    content_blocks: List[Dict[str, Any]] = field(default_factory=list)
    options: List[str] = field(default_factory=list)
    image_refs: List[str] = field(default_factory=list)
    page_indices: List[int] = field(default_factory=list)
    region_keys: List[tuple[int, int]] = field(default_factory=list)
    has_formula: bool = False
    has_image: bool = False

    def add_segment(self, segment: SplitSegment) -> None:
        if segment.page_index not in self.page_indices:
            self.page_indices.append(segment.page_index)
        if segment.region_key and segment.region_key not in self.region_keys:
            self.region_keys.append(segment.region_key)

        if segment.label in {"image", "chart"}:
            self.has_image = True
            if segment.content:
                self.image_refs.append(segment.content)
                self.content_blocks.append({
                    "block_type": "image",
                    "content": segment.content,
                })
            return

        if segment.label == "formula":
            self.has_formula = True

        if segment.content:
            self.content_blocks.append({
                "block_type": "text",
                "content": segment.content,
            })
