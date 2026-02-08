"""
题目分割结构化输出 Schema
使用 Pydantic 模型定义，配合 LangChain ToolStrategy 实现结构化输出
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """题目内容块"""
    block_type: Literal["text", "image"] = Field(description="内容类型：text 或 image")
    content: str = Field(description="文本内容（公式用 LaTeX 标记：行内 $...$，独占行 $$...$$）或图片路径")


class Question(BaseModel):
    """单道题目"""
    question_id: str = Field(description="题号，如 '1', '2', '(1)' 等")
    question_type: Literal["选择题", "填空题", "解答题", "判断题"] = Field(description="题目类型")
    content_blocks: List[ContentBlock] = Field(description="题干内容块列表（不含选项）")
    options: Optional[List[str]] = Field(default=None, description="选项列表，仅选择题需要，如 ['A. xxx', 'B. yyy']")
    has_formula: bool = Field(default=False, description="是否包含数学公式")
    has_image: bool = Field(default=False, description="是否包含图片")
    image_refs: Optional[List[str]] = Field(default=None, description="图片引用路径列表")


class QuestionSplitResult(BaseModel):
    """题目分割结果"""
    questions: List[Question] = Field(description="分割后的题目列表")
