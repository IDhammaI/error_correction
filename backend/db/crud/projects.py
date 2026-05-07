"""Project CRUD helpers."""

from typing import List, Optional

from sqlalchemy.orm import Session

from db.models import Note, Project, Question, UploadBatch


VALID_PROJECT_TYPES = {"question", "note"}


def normalize_project_type(project_type=None) -> str:
    value = (project_type or "question").strip().lower()
    return value if value in VALID_PROJECT_TYPES else "question"


def serialize_project(project: Project) -> dict:
    return {
        "id": project.id,
        "public_id": project.public_id,
        "name": project.name,
        "project_type": normalize_project_type(getattr(project, "project_type", None)),
        "description": project.description or "",
        "color": project.color or "#2563eb",
        "icon": project.icon or "book-open",
        "is_default": bool(project.is_default),
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def get_projects(db: Session, user_id=None, project_type=None) -> List[Project]:
    query = db.query(Project)
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    else:
        query = query.filter(Project.user_id == None)
    if project_type:
        query = query.filter(Project.project_type == normalize_project_type(project_type))
    query = query.filter(Project.is_default == False)
    return query.order_by(Project.project_type.asc(), Project.updated_at.desc(), Project.id.desc()).all()


def get_project(db: Session, project_id: int, user_id=None) -> Optional[Project]:
    if not project_id:
        return None
    query = db.query(Project).filter(Project.id == project_id)
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    else:
        query = query.filter(Project.user_id == None)
    return query.first()


def create_project(
    db: Session,
    name: str,
    user_id=None,
    description: str = "",
    color: str = "#2563eb",
    icon: str = "book-open",
    is_default: bool = False,
    project_type: str = "question",
) -> Project:
    project_type = normalize_project_type(project_type)
    project = Project(
        user_id=user_id,
        name=(name or "").strip()[:100],
        project_type=project_type,
        description=(description or "").strip()[:1000],
        color=(color or "#2563eb").strip()[:20],
        icon=(icon or "book-open").strip()[:50],
        is_default=is_default,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def resolve_project_id(db: Session, project_id=None, user_id=None, project_type: str = "question") -> int:
    project_type = normalize_project_type(project_type)
    if not project_id:
        raise ValueError("PROJECT_REQUIRED")
    project = get_project(db, int(project_id), user_id=user_id)
    if not project:
        raise ValueError("PROJECT_NOT_FOUND")
    if normalize_project_type(project.project_type) != project_type:
        raise ValueError("PROJECT_TYPE_MISMATCH")
    return project.id


def require_project_id(db: Session, project_id, user_id=None, project_type=None) -> int:
    project = get_project(db, int(project_id), user_id=user_id) if project_id else None
    if not project:
        raise ValueError("PROJECT_NOT_FOUND")
    if project_type and normalize_project_type(project.project_type) != normalize_project_type(project_type):
        raise ValueError("PROJECT_TYPE_MISMATCH")
    return project.id


def update_project(db: Session, project_id: int, user_id=None, name: str = None) -> Optional[Project]:
    project = get_project(db, project_id, user_id=user_id)
    if not project:
        return None
    if project.is_default:
        raise ValueError("DEFAULT_PROJECT_IMMUTABLE")
    if name is not None:
        project.name = name.strip()[:100]
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id=None) -> bool:
    project = get_project(db, project_id, user_id=user_id)
    if not project:
        return False
    if project.is_default:
        raise ValueError("DEFAULT_PROJECT_IMMUTABLE")
    has_questions = db.query(Question.id).filter(Question.project_id == project.id).first()
    has_notes = db.query(Note.id).filter(Note.project_id == project.id).first()
    has_batches = db.query(UploadBatch.id).filter(UploadBatch.project_id == project.id).first()
    if has_questions or has_notes or has_batches:
        raise ValueError("PROJECT_NOT_EMPTY")
    db.delete(project)
    db.commit()
    return True
