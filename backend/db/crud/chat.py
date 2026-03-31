"""教学辅导对话 CRUD"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from db.models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


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
