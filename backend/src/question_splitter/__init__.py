"""Rule-based question splitter backed by Baidu paper_cut_edu regions."""

from .build_questions import build_questions_from_ocr

__all__ = ["build_questions_from_ocr"]
