"""Workflow run CRUD helpers."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from db.models import WorkflowRun


def create_workflow_run(
    db: Session,
    *,
    user_id=None,
    run_type: str = "split",
    status: str = "pending",
    public_id: str | None = None,
    subject: str | None = None,
    model_provider: str | None = None,
    file_names: list[str] | None = None,
    result_dir: str = "",
    question_count: int = 0,
) -> WorkflowRun:
    run = WorkflowRun(
        public_id=public_id or str(uuid.uuid4()),
        user_id=user_id,
        run_type=run_type,
        status=status,
        subject=subject,
        model_provider=model_provider,
        file_names_json=json.dumps(file_names or [], ensure_ascii=False),
        result_dir=result_dir,
        question_count=question_count,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_workflow_run(
    db: Session,
    public_id: str,
    *,
    user_id=None,
    run_type: str | None = None,
) -> Optional[WorkflowRun]:
    query = db.query(WorkflowRun).filter(WorkflowRun.public_id == public_id)
    if user_id is not None:
        query = query.filter(WorkflowRun.user_id == user_id)
    if run_type:
        query = query.filter(WorkflowRun.run_type == run_type)
    return query.first()


def get_latest_workflow_run(
    db: Session,
    *,
    user_id=None,
    run_type: str | None = None,
    status: str | None = None,
) -> Optional[WorkflowRun]:
    query = db.query(WorkflowRun)
    if user_id is not None:
        query = query.filter(WorkflowRun.user_id == user_id)
    if run_type:
        query = query.filter(WorkflowRun.run_type == run_type)
    if status:
        query = query.filter(WorkflowRun.status == status)
    return query.order_by(WorkflowRun.created_at.desc()).first()


def update_workflow_run(
    db: Session,
    public_id: str,
    *,
    user_id=None,
    **fields,
) -> Optional[WorkflowRun]:
    run = get_workflow_run(db, public_id, user_id=user_id)
    if not run:
        return None

    allowed = {
        "status",
        "subject",
        "model_provider",
        "result_dir",
        "question_count",
        "error_message",
    }
    for key, value in fields.items():
        if key in allowed:
            setattr(run, key, value)
    if "file_names" in fields:
        run.file_names_json = json.dumps(fields["file_names"] or [], ensure_ascii=False)
    run.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run


def serialize_workflow_run(run: WorkflowRun) -> dict:
    return {
        "id": run.id,
        "run_id": run.public_id,
        "user_id": run.user_id,
        "run_type": run.run_type,
        "status": run.status,
        "subject": run.subject,
        "model_provider": run.model_provider,
        "file_names": json.loads(run.file_names_json) if run.file_names_json else [],
        "result_dir": run.result_dir,
        "question_count": run.question_count,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }
