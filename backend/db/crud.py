"""
数据库 CRUD 操作
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import UploadBatch, Question, KnowledgeTag, QuestionTagMapping


def compute_content_hash(content_blocks: List[Dict]) -> str:
    """
    基于 content_blocks 计算去重哈希
    使用题目文本内容计算 SHA256
    """
    text_parts = []
    for block in content_blocks:
        if block.get("block_type") == "text":
            text_parts.append(block.get("content", ""))

    text = " ".join(text_parts).strip()
    if not text:
        # 如果没有文本内容，使用整个 content_blocks 的 JSON 作为哈希源
        text = json.dumps(content_blocks, ensure_ascii=False)

    return hashlib.sha256(text.encode()).hexdigest()


def detect_subject(questions: List[Dict]) -> str:
    """
    AI 识别科目：基于 knowledge_tags 和内容推断
    """
    # 科目关键词映射
    math_tags = {"复数", "函数", "三角函数", "数列", "立体几何", "圆锥曲线",
                 "概率", "统计", "导数", "不等式", "向量", "集合", "算法",
                 "平面几何", "解析几何", "极限", "积分", "矩阵"}

    physics_tags = {"力学", "电学", "光学", "热学", "电磁学", "机械波",
                    "动量", "能量", "电路", "磁场", "电场", "重力"}

    chemistry_tags = {"化学方程式", "有机化学", "无机化学", "氧化还原",
                      "离子反应", "化学平衡", "电化学", "物质结构"}

    biology_tags = {"细胞", "遗传", "进化", "生态", "代谢", "基因",
                    "光合作用", "呼吸作用"}

    english_tags = {"语法", "词汇", "阅读理解", "完形填空", "写作", "听力"}

    chinese_tags = {"文言文", "现代文", "古诗", "作文", "修辞", "阅读"}

    # 收集所有标签
    all_tags = set()
    for q in questions:
        tags = q.get("knowledge_tags") or []
        all_tags.update(tags)

    # 匹配科目
    if all_tags & math_tags:
        return "数学"
    if all_tags & physics_tags:
        return "物理"
    if all_tags & chemistry_tags:
        return "化学"
    if all_tags & biology_tags:
        return "生物"
    if all_tags & english_tags:
        return "英语"
    if all_tags & chinese_tags:
        return "语文"

    # 如果标签匹配失败，尝试从内容中推断
    for q in questions:
        content_text = ""
        for block in q.get("content_blocks", []):
            if block.get("block_type") == "text":
                content_text += block.get("content", "")

        # 检查数学公式标记
        if "$$" in content_text or "$" in content_text:
            return "数学"

        # 检查化学符号
        if any(sym in content_text for sym in ["→", "⇌", "↑", "↓"]):
            # 更多化学特征判断
            chem_elements = ["H₂", "O₂", "Na", "Cl", "Ca", "Fe", "Cu", "Zn"]
            if any(el in content_text for el in chem_elements):
                return "化学"

        # 检查物理单位
        physics_units = ["m/s", "kg", "N", "J", "W", "V", "A", "Ω", "Hz"]
        if any(unit in content_text for unit in physics_units):
            return "物理"

    return "未知"


def get_or_create_tag(db: Session, tag_name: str, subject: str) -> KnowledgeTag:
    """获取或创建知识点标签"""
    tag = db.query(KnowledgeTag).filter_by(
        tag_name=tag_name,
        subject=subject
    ).first()

    if not tag:
        tag = KnowledgeTag(tag_name=tag_name, subject=subject)
        db.add(tag)
        db.flush()

    return tag


def question_exists(db: Session, content_hash: str) -> Optional[Question]:
    """检查题目是否已存在（通过内容哈希）"""
    return db.query(Question).filter_by(content_hash=content_hash).first()


def save_questions_to_db(
    db: Session,
    questions: List[Dict],
    batch_info: Dict[str, Any]
) -> Dict[str, int]:
    """
    批量入库题目

    Args:
        db: 数据库会话
        questions: 题目列表（字典格式，来自 questions.json）
        batch_info: 批次信息，包含 original_filename, file_path 等

    Returns:
        dict: {"created": 新增数量, "duplicates": 重复数量}
    """
    # 检测科目
    subject = batch_info.get("subject") or detect_subject(questions)

    # 创建批次记录
    batch = UploadBatch(
        original_filename=batch_info.get("original_filename", "未知"),
        subject=subject,
        file_path=batch_info.get("file_path", ""),
        upload_time=batch_info.get("upload_time") or datetime.utcnow()
    )
    db.add(batch)
    db.flush()  # 获取 batch.id

    created = 0
    duplicates = 0

    for q in questions:
        content_blocks = q.get("content_blocks", [])
        if not content_blocks:
            continue

        content_hash = compute_content_hash(content_blocks)

        # 检查是否已存在
        if question_exists(db, content_hash):
            duplicates += 1
            continue

        # 创建题目记录
        question = Question(
            batch_id=batch.id,
            content_hash=content_hash,
            question_type=q.get("question_type"),
            content_json=json.dumps(content_blocks, ensure_ascii=False),
            options_json=json.dumps(q.get("options"), ensure_ascii=False) if q.get("options") else None,
            has_formula=q.get("has_formula", False),
            has_image=q.get("has_image", False),
            image_refs_json=json.dumps(q.get("image_refs"), ensure_ascii=False) if q.get("image_refs") else None,
            needs_correction=q.get("needs_correction", False),
            ocr_issues_json=json.dumps(q.get("ocr_issues"), ensure_ascii=False) if q.get("ocr_issues") else None
        )
        db.add(question)
        db.flush()

        # 处理知识点标签
        knowledge_tags = q.get("knowledge_tags") or []
        for tag_name in knowledge_tags:
            tag = get_or_create_tag(db, tag_name, subject)
            mapping = QuestionTagMapping(
                question_id=question.id,
                tag_id=tag.id
            )
            db.add(mapping)

        created += 1

    db.commit()

    return {"created": created, "duplicates": duplicates}


def get_questions_by_subject(
    db: Session,
    subject: str,
    limit: int = 100,
    offset: int = 0
) -> List[Question]:
    """按科目查询题目"""
    return db.query(Question).join(UploadBatch).filter(
        UploadBatch.subject == subject
    ).order_by(Question.created_at.desc()).offset(offset).limit(limit).all()


def get_questions_by_tag(
    db: Session,
    tag_name: str,
    limit: int = 100,
    offset: int = 0
) -> List[Question]:
    """按标签查询题目"""
    return db.query(Question).join(QuestionTagMapping).join(KnowledgeTag).filter(
        KnowledgeTag.tag_name == tag_name
    ).order_by(Question.created_at.desc()).offset(offset).limit(limit).all()


def get_all_tags(db: Session, subject: Optional[str] = None) -> List[KnowledgeTag]:
    """获取所有标签（可按科目筛选）"""
    query = db.query(KnowledgeTag)
    if subject:
        query = query.filter(KnowledgeTag.subject == subject)
    return query.order_by(KnowledgeTag.tag_name).all()


def get_statistics(db: Session) -> Dict[str, Any]:
    """获取统计信息"""
    total_questions = db.query(func.count(Question.id)).scalar()
    total_batches = db.query(func.count(UploadBatch.id)).scalar()
    total_tags = db.query(func.count(KnowledgeTag.id)).scalar()

    # 按科目统计
    subject_stats = db.query(
        UploadBatch.subject,
        func.count(Question.id)
    ).join(Question).group_by(UploadBatch.subject).all()

    return {
        "total_questions": total_questions or 0,
        "total_batches": total_batches or 0,
        "total_tags": total_tags or 0,
        "by_subject": {s: c for s, c in subject_stats}
    }
