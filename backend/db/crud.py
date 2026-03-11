"""
数据库 CRUD 操作
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func

logger = logging.getLogger(__name__)

from db.models import UploadBatch, Question, KnowledgeTag, QuestionTagMapping, ChatSession, ChatMessage


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


def get_existing_subjects(db: Session) -> List[str]:
    """获取数据库中已有的所有科目名称（去重）"""
    rows = db.query(UploadBatch.subject).distinct().filter(
        UploadBatch.subject.isnot(None),
        UploadBatch.subject != "",
    ).all()
    return [r[0] for r in rows]


def get_existing_tag_names(db: Session, subject: Optional[str] = None) -> List[str]:
    """获取数据库中已有的知识点标签名称列表（字符串）"""
    query = db.query(KnowledgeTag.tag_name).distinct()
    if subject:
        query = query.filter(KnowledgeTag.subject == subject)
    rows = query.order_by(KnowledgeTag.tag_name).all()
    return [r[0] for r in rows]


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
    # 科目由编排智能体识别，不再使用关键词匹配
    subject = batch_info.get("subject") or "未知"

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
            ocr_issues_json=json.dumps(q.get("ocr_issues"), ensure_ascii=False) if q.get("ocr_issues") else None,
            answer=q.get("answer") or None,
            user_answer=q.get("user_answer") or None,
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


def get_history_questions(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Question], int]:
    """
    分页查询历史题目（全部题目）

    Args:
        db: 数据库会话
        start_date: 开始日期筛选
        end_date: 结束日期筛选
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        (题目列表, 总数)
    """
    query = db.query(Question).join(UploadBatch)

    if start_date:
        query = query.filter(UploadBatch.upload_time >= start_date)
    if end_date:
        query = query.filter(UploadBatch.upload_time <= end_date)

    # 获取总数
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    questions = (
        query.options(selectinload(Question.batch), selectinload(Question.tags).selectinload(QuestionTagMapping.tag))
        .order_by(Question.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return questions, total


def search_questions(
    db: Session,
    keyword: Optional[str] = None,
    knowledge_tag: Optional[str] = None,
    question_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Question], int]:
    """
    搜索题目（知识点/题型/关键字）

    Args:
        db: 数据库会话
        keyword: 关键字搜索（匹配题目内容 content_json）
        knowledge_tag: 知识点标签筛选
        question_type: 题型筛选
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        (题目列表, 总数)
    """
    query = db.query(Question)

    # 关键字搜索：匹配 content_json 中的内容
    if keyword:
        escaped = re.sub(r"([%_\\])", r"\\\1", keyword)
        query = query.filter(Question.content_json.ilike(f"%{escaped}%"))

    # 题型筛选
    if question_type:
        query = query.filter(Question.question_type == question_type)

    # 知识点标签筛选（支持逗号分隔多选）
    if knowledge_tag:
        tag_list = [t.strip() for t in knowledge_tag.split(',') if t.strip()]
        if len(tag_list) == 1:
            query = query.join(QuestionTagMapping).join(KnowledgeTag).filter(
                KnowledgeTag.tag_name == tag_list[0]
            )
        elif tag_list:
            query = query.join(QuestionTagMapping).join(KnowledgeTag).filter(
                KnowledgeTag.tag_name.in_(tag_list)
            )

    # 获取总数（需要先去除distinct，因为join可能产生重复）
    total = query.distinct().count()

    # 分页查询
    offset = (page - 1) * page_size
    questions = (
        query.distinct()
        .options(selectinload(Question.batch), selectinload(Question.tags).selectinload(QuestionTagMapping.tag))
        .order_by(Question.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return questions, total


def get_knowledge_stats(db: Session) -> List[Dict]:
    """
    获取知识点统计信息

    Returns:
        [{"tag_name": "xxx", "count": 10}, ...]
    """
    stats = db.query(
        KnowledgeTag.tag_name,
        func.count(QuestionTagMapping.question_id).label("count")
    ).join(
        QuestionTagMapping, QuestionTagMapping.tag_id == KnowledgeTag.id
    ).group_by(
        KnowledgeTag.id, KnowledgeTag.tag_name
    ).order_by(
        func.count(QuestionTagMapping.question_id).desc()
    ).all()

    return [{"tag_name": tag_name, "count": count} for tag_name, count in stats]


def delete_question(db: Session, question_id: int) -> bool:
    """
    删除题目

    Args:
        db: 数据库会话
        question_id: 题目ID

    Returns:
        是否删除成功
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return False

    try:
        # 删除关联的标签映射
        db.query(QuestionTagMapping).filter(QuestionTagMapping.question_id == question_id).delete()

        # 删除题目
        db.delete(question)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除题目 {question_id} 失败: {e}")
        raise

    return True


def query_questions(
    db: Session,
    subject: Optional[str] = None,
    knowledge_tag: Optional[str] = None,
    question_type: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    review_status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Question], int]:
    """
    统一查询题目（合并 get_history_questions 和 search_questions 的能力）

    支持所有筛选条件任意组合。
    """
    query = db.query(Question).join(UploadBatch)

    if subject:
        query = query.filter(UploadBatch.subject == subject)

    if question_type:
        query = query.filter(Question.question_type == question_type)

    if keyword:
        escaped = re.sub(r"([%_\\])", r"\\\1", keyword)
        query = query.filter(Question.content_json.ilike(f"%{escaped}%"))

    if knowledge_tag:
        tag_list = [t.strip() for t in knowledge_tag.split(',') if t.strip()]
        if len(tag_list) == 1:
            query = query.join(QuestionTagMapping).join(KnowledgeTag).filter(
                KnowledgeTag.tag_name == tag_list[0]
            )
        elif tag_list:
            query = query.join(QuestionTagMapping).join(KnowledgeTag).filter(
                KnowledgeTag.tag_name.in_(tag_list)
            )

    if start_date:
        query = query.filter(Question.created_at >= start_date)
    if end_date:
        query = query.filter(Question.created_at <= end_date)

    if review_status:
        query = query.filter(Question.review_status == review_status)

    total = query.distinct().count()

    offset = (page - 1) * page_size
    questions = (
        query.distinct()
        .options(selectinload(Question.batch), selectinload(Question.tags).selectinload(QuestionTagMapping.tag))
        .order_by(Question.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return questions, total


def update_user_answer(db: Session, question_id: int, user_answer: str) -> Optional[Question]:
    """更新用户答案"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return None

    try:
        question.user_answer = user_answer
        question.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        return question
    except Exception as e:
        db.rollback()
        logger.error(f"更新题目 {question_id} 答案失败: {e}")
        raise


def get_existing_question_types(db: Session) -> List[str]:
    """获取数据库中已有的所有题型（去重）"""
    rows = db.query(Question.question_type).distinct().filter(
        Question.question_type.isnot(None),
        Question.question_type != "",
    ).all()
    return [r[0] for r in rows]


def get_questions_by_ids(db: Session, question_ids: List[int]) -> List[Question]:
    """按 ID 列表批量查询题目"""
    if not question_ids:
        return []
    return (
        db.query(Question)
        .options(joinedload(Question.batch), joinedload(Question.tags).joinedload(QuestionTagMapping.tag))
        .filter(Question.id.in_(question_ids))
        .all()
    )


VALID_REVIEW_STATUSES = ('待复习', '复习中', '已掌握')


def update_review_status(db: Session, question_id: int, review_status: str) -> Optional[Question]:
    """更新题目复习状态"""
    if review_status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"无效的复习状态: {review_status}，可选值: {VALID_REVIEW_STATUSES}")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return None

    try:
        question.review_status = review_status
        question.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        return question
    except Exception as e:
        db.rollback()
        logger.error(f"更新题目 {question_id} 复习状态失败: {e}")
        raise


def get_review_status_stats(db: Session) -> Dict[str, int]:
    """按复习状态分组统计数量"""
    rows = db.query(
        Question.review_status,
        func.count(Question.id)
    ).group_by(Question.review_status).all()

    result = {'待复习': 0, '复习中': 0, '已掌握': 0}
    for status, count in rows:
        key = status or '待复习'
        if key in result:
            result[key] += count
        else:
            result['待复习'] += count
    return result


def get_daily_counts(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """获取最近 N 天每日新增题目数"""
    from datetime import timedelta
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)

    # SQLite 兼容：使用 func.date() 提取日期字符串
    date_expr = func.date(Question.created_at)
    rows = db.query(
        date_expr.label('date'),
        func.count(Question.id).label('count')
    ).filter(
        Question.created_at >= cutoff
    ).group_by(
        date_expr
    ).order_by(
        date_expr
    ).all()

    # 构建日期→数量映射
    date_map = {str(row.date): row.count for row in rows}

    # 填充缺失的日期
    result = []
    for i in range(days):
        d = cutoff + timedelta(days=i)
        date_key = d.strftime('%Y-%m-%d')
        date_str = d.strftime('%m-%d')
        result.append({'date': date_str, 'count': date_map.get(date_key, 0)})

    return result


# ============================================================
# 教学辅导对话 CRUD
# ============================================================


def update_question_answer(db: Session, question_id: int, answer: str) -> Optional[Question]:
    """保存/更新题目答案（Markdown 格式）"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return None

    try:
        question.answer = answer
        question.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        return question
    except Exception as e:
        db.rollback()
        logger.error(f"保存题目 {question_id} 答案失败: {e}")
        raise


def create_chat_session(db: Session, question_id: int) -> ChatSession:
    """为题目创建新的对话会话"""
    session = ChatSession(question_id=question_id)
    db.add(session)
    try:
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        logger.error(f"创建对话会话失败: {e}")
        raise


_VALID_ROLES = ('user', 'assistant')


def add_chat_message(db: Session, session_id: int, role: str, content: str) -> ChatMessage:
    """向对话中追加一条消息"""
    if role not in _VALID_ROLES:
        raise ValueError(f"无效的消息角色: {role}（可选: {', '.join(_VALID_ROLES)}）")
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    try:
        # 同步更新会话的 updated_at（直接 UPDATE 避免加载整行）
        db.query(ChatSession).filter(ChatSession.id == session_id).update(
            {"updated_at": datetime.utcnow()}, synchronize_session=False
        )
        db.commit()
        db.refresh(msg)
        return msg
    except Exception as e:
        db.rollback()
        logger.error(f"添加对话消息失败: {e}")
        raise


def get_chat_messages(
    db: Session,
    session_id: int,
    limit: int = 30,
    before_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    游标分页获取对话消息

    Args:
        session_id: 会话 ID
        limit: 每次返回的消息数
        before_id: 游标，返回 ID 小于此值的消息

    Returns:
        {"messages": [...], "hasMore": bool}
    """
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    if before_id:
        query = query.filter(ChatMessage.id < before_id)

    # 按 ID 降序取 limit+1 条，判断是否还有更早消息
    rows = query.order_by(ChatMessage.id.desc()).limit(limit + 1).all()

    has_more = len(rows) > limit
    messages = rows[:limit]
    messages.reverse()  # 恢复正序

    return {
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ],
        "hasMore": has_more,
    }


def get_chat_sessions_by_question(db: Session, question_id: int, limit: int = 50) -> List[ChatSession]:
    """获取某道题目的对话会话（按更新时间降序，默认最多 50 条）"""
    return (
        db.query(ChatSession)
        .filter(ChatSession.question_id == question_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_all_chat_sessions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[ChatSession], int]:
    """分页获取所有对话会话"""
    query = db.query(ChatSession)
    total = query.count()
    offset = (page - 1) * page_size
    sessions = (
        query.options(selectinload(ChatSession.question))
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return sessions, total
