"""Spaced-repetition scheduling helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from db.models import KnowledgeTag, Note, NoteTagMapping, Question, QuestionTagMapping, ReviewEvent


RATING_QUALITY = {
    "again": 1,
    "hard": 3,
    "good": 4,
    "easy": 5,
    "忘记": 1,
    "困难": 3,
    "掌握": 4,
    "简单": 5,
}


def normalize_rating(rating: str | int | None) -> tuple[str, int]:
    if isinstance(rating, int):
        quality = max(0, min(5, rating))
        label = {0: "again", 1: "again", 2: "again", 3: "hard", 4: "good", 5: "easy"}[quality]
        return label, quality

    label = str(rating or "good").strip()
    if label.isdigit():
        return normalize_rating(int(label))
    if label not in RATING_QUALITY:
        raise ValueError("INVALID_REVIEW_RATING")
    return label, RATING_QUALITY[label]


def _sm2_next(target: Any, quality: int) -> tuple[int, float]:
    previous_count = int(getattr(target, "review_count", 0) or 0)
    previous_interval = int(getattr(target, "review_interval_days", 0) or 0)
    previous_ease = float(getattr(target, "ease_factor", 2.5) or 2.5)

    ease = max(1.3, previous_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if quality < 3:
        return 1, ease
    if previous_count <= 0:
        return 1, ease
    if previous_count == 1:
        return 6, ease
    return max(1, round(previous_interval * ease)), ease


def compute_review_priority(target: Any, now: Optional[datetime] = None) -> int:
    """Return 0-100 priority. Due or overdue items move to the top."""
    now = now or datetime.utcnow()
    due_at = getattr(target, "review_due_at", None)
    review_count = int(getattr(target, "review_count", 0) or 0)
    interval_days = int(getattr(target, "review_interval_days", 0) or 0)
    status = getattr(target, "review_status", None)

    if due_at:
        delta_days = (now - due_at).total_seconds() / 86400
        if delta_days >= 0:
            return max(72, min(99, round(82 + delta_days * 4)))
        return max(12, min(70, round(58 + delta_days * 8)))

    if status == "待复习":
        return 68
    if review_count <= 0:
        return 56
    return max(8, min(55, 48 - min(interval_days, 30)))


def serialize_review_fields(target: Any) -> dict:
    priority = compute_review_priority(target)
    due_at = getattr(target, "review_due_at", None)
    now = datetime.utcnow()
    return {
        "review_due_at": due_at.isoformat() if due_at else None,
        "review_last_at": getattr(target, "review_last_at", None).isoformat()
        if getattr(target, "review_last_at", None)
        else None,
        "review_interval_days": int(getattr(target, "review_interval_days", 0) or 0),
        "review_count": int(getattr(target, "review_count", 0) or 0),
        "ease_factor": round(float(getattr(target, "ease_factor", 2.5) or 2.5), 2),
        "review_priority": priority,
        "review_is_due": not due_at or due_at <= now,
    }


def schedule_question_review(db: Session, question_id: int, rating=None, user_id=None) -> Optional[Question]:
    query = db.query(Question).filter(Question.id == question_id)
    if user_id is not None:
        query = query.filter(Question.user_id == user_id)
    question = query.first()
    if not question:
        return None
    _schedule_target(db, question, "question", rating=rating, user_id=question.user_id)
    db.commit()
    db.refresh(question)
    return question


def schedule_note_review(db: Session, note_id: int, rating=None, user_id=None) -> Optional[Note]:
    query = db.query(Note).filter(Note.id == note_id)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    note = query.first()
    if not note:
        return None
    _schedule_target(db, note, "note", rating=rating, user_id=note.user_id)
    db.commit()
    db.refresh(note)
    return note


def _schedule_target(db: Session, target: Any, target_type: str, rating=None, user_id=None):
    label, quality = normalize_rating(rating)
    now = datetime.utcnow()
    interval_days, ease = _sm2_next(target, quality)
    next_due_at = now + timedelta(days=interval_days)

    target.review_last_at = now
    target.review_due_at = next_due_at
    target.review_interval_days = interval_days
    target.review_count = int(getattr(target, "review_count", 0) or 0) + 1
    target.ease_factor = ease
    if hasattr(target, "updated_at"):
        target.updated_at = now
    if hasattr(target, "review_status"):
        target.review_status = "待复习" if quality < 3 else "已掌握"

    db.add(
        ReviewEvent(
            user_id=user_id,
            target_type=target_type,
            target_id=target.id,
            rating=label,
            quality=quality,
            interval_days=interval_days,
            ease_factor=ease,
            reviewed_at=now,
            next_due_at=next_due_at,
        )
    )


def get_due_reviews(db: Session, user_id=None, target_type="all", limit=40, project_id=None) -> dict:
    now = datetime.utcnow()
    limit = max(1, min(100, int(limit or 40)))
    payload = {"questions": [], "notes": []}

    if target_type in ("all", "question", "questions"):
        query = (
            db.query(Question)
            .options(selectinload(Question.batch), selectinload(Question.tags).selectinload(QuestionTagMapping.tag))
            .filter(or_(Question.review_due_at == None, Question.review_due_at <= now))
        )
        if user_id is not None:
            query = query.filter(Question.user_id == user_id)
        if project_id is not None:
            query = query.filter(Question.project_id == project_id)
        payload["questions"] = (
            query.order_by(Question.review_due_at.isnot(None), Question.review_due_at.asc(), Question.updated_at.desc())
            .limit(limit)
            .all()
        )

    if target_type in ("all", "note", "notes"):
        query = (
            db.query(Note)
            .options(selectinload(Note.tags).selectinload(NoteTagMapping.tag))
            .filter(or_(Note.review_due_at == None, Note.review_due_at <= now))
        )
        if user_id is not None:
            query = query.filter(Note.user_id == user_id)
        if project_id is not None:
            query = query.filter(Note.project_id == project_id)
        payload["notes"] = (
            query.order_by(Note.review_due_at.isnot(None), Note.review_due_at.asc(), Note.updated_at.desc())
            .limit(limit)
            .all()
        )

    return payload
