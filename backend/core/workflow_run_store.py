"""Workflow run storage adapter.

Routes should use this module instead of touching WorkflowRun CRUD and
filesystem paths directly. Today the backing store is SQLite + local files;
later Redis can replace these functions without changing route behavior.
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from core.config import settings
from db import crud
from db.models import WorkflowRun

RUN_TYPE_SPLIT = "split"

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

WRONGBOOK_SUFFIX = "_wrongbook.md"


def _user_key(user_id) -> str:
    return str(user_id) if user_id is not None else "anon"


def build_run_result_dir(user_id, run_id: str) -> Path:
    return settings.runs_dir / _user_key(user_id) / run_id


def create_split_run(
    db,
    *,
    user_id,
    file_names: list[str],
    model_provider: str,
    status: str = STATUS_RUNNING,
) -> WorkflowRun:
    run_id = str(uuid.uuid4())
    result_dir = build_run_result_dir(user_id, run_id)
    result_dir.mkdir(parents=True, exist_ok=True)
    return crud.create_workflow_run(
        db,
        user_id=user_id,
        run_type=RUN_TYPE_SPLIT,
        status=status,
        public_id=run_id,
        model_provider=model_provider,
        file_names=file_names,
        result_dir=str(result_dir),
    )


def get_split_run(db, run_id: str, *, user_id) -> Optional[WorkflowRun]:
    if not run_id:
        return None
    return crud.get_workflow_run(
        db,
        run_id,
        user_id=user_id,
        run_type=RUN_TYPE_SPLIT,
    )


def get_latest_split_run(db, *, user_id, status: str | None = None) -> Optional[WorkflowRun]:
    return crud.get_latest_workflow_run(
        db,
        user_id=user_id,
        run_type=RUN_TYPE_SPLIT,
        status=status,
    )


def wrongbook_filename(run: WorkflowRun) -> str:
    return f"{run.public_id}{WRONGBOOK_SUFFIX}"


def run_id_from_wrongbook_filename(filename: str) -> str | None:
    if not filename or "/" in filename or "\\" in filename:
        return None
    if not filename.endswith(WRONGBOOK_SUFFIX):
        return None
    run_id = filename[: -len(WRONGBOOK_SUFFIX)]
    return run_id or None


def get_split_run_by_wrongbook_filename(
    db,
    filename: str,
    *,
    user_id,
) -> Optional[WorkflowRun]:
    run_id = run_id_from_wrongbook_filename(filename)
    if not run_id:
        return None
    return get_split_run(db, run_id, user_id=user_id)


def mark_succeeded(
    db,
    run_id: str,
    *,
    user_id,
    subject: str | None,
    question_count: int,
) -> Optional[WorkflowRun]:
    return crud.update_workflow_run(
        db,
        run_id,
        user_id=user_id,
        status=STATUS_SUCCEEDED,
        subject=subject,
        question_count=question_count,
        error_message=None,
    )


def mark_failed(db, run_id: str, *, user_id, error_message: str) -> Optional[WorkflowRun]:
    return crud.update_workflow_run(
        db,
        run_id,
        user_id=user_id,
        status=STATUS_FAILED,
        error_message=(error_message or "")[:2000],
    )


def questions_path(run: WorkflowRun) -> Path:
    return Path(run.result_dir) / "questions.json"


def metadata_path(run: WorkflowRun) -> Path:
    return Path(run.result_dir) / "split_metadata.json"


def wrongbook_path(run: WorkflowRun) -> Path:
    return Path(run.result_dir) / wrongbook_filename(run)


def read_questions(run: WorkflowRun) -> list[dict]:
    path = questions_path(run)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_subject(run: WorkflowRun) -> str | None:
    path = metadata_path(run)
    if not path.exists():
        return run.subject
    with path.open("r", encoding="utf-8") as f:
        return json.load(f).get("subject") or run.subject
