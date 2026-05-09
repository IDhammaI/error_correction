"""Project routes."""

import logging

from flask import Blueprint, jsonify, request, session

from db import SessionLocal
from db import crud
from db.models import Note, Question

logger = logging.getLogger(__name__)

bp = Blueprint("projects", __name__)


def _project_owner_id():
    return session.get("user_id")


def _serialize_project_with_counts(db, project):
    payload = crud.serialize_project(project)
    payload["question_count"] = db.query(Question).filter(Question.project_id == project.id).count()
    payload["note_count"] = db.query(Note).filter(Note.project_id == project.id).count()
    return payload


@bp.route("/projects", methods=["GET"])
def list_projects():
    try:
        with SessionLocal() as db:
            user_id = _project_owner_id()
            project_type = request.args.get("project_type") or request.args.get("type") or None
            projects = crud.get_projects(db, user_id=user_id, project_type=project_type)
            return jsonify({
                "success": True,
                "projects": [_serialize_project_with_counts(db, p) for p in projects],
            })
    except Exception:
        logger.exception("list projects failed")
        return jsonify({"success": False, "error": "获取项目列表失败"}), 500


@bp.route("/projects", methods=["POST"])
def create_project():
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        project_type = crud.normalize_project_type(data.get("project_type") or data.get("type"))
        if not name:
            return jsonify({"success": False, "error": "项目名称不能为空"}), 400
        if len(name) > 100:
            return jsonify({"success": False, "error": "项目名称不能超过 100 个字符"}), 400

        with SessionLocal() as db:
            project = crud.create_project(
                db,
                name=name,
                user_id=_project_owner_id(),
                description=data.get("description") or "",
                color=data.get("color") or "#2563eb",
                icon=data.get("icon") or ("book-open" if project_type == "note" else "database"),
                project_type=project_type,
            )
            payload = _serialize_project_with_counts(db, project)
            return jsonify({
                "success": True,
                "project": payload,
            }), 201
    except Exception:
        logger.exception("create project failed")
        return jsonify({"success": False, "error": "创建项目失败"}), 500


@bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"success": False, "error": "项目名称不能为空"}), 400
        if len(name) > 100:
            return jsonify({"success": False, "error": "项目名称不能超过 100 个字符"}), 400

        with SessionLocal() as db:
            try:
                project = crud.update_project(db, project_id, user_id=_project_owner_id(), name=name)
            except ValueError as exc:
                if str(exc) == "DEFAULT_PROJECT_IMMUTABLE":
                    return jsonify({"success": False, "error": "默认项目不能重命名"}), 400
                raise
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404
            return jsonify({"success": True, "project": _serialize_project_with_counts(db, project)})
    except Exception:
        logger.exception("update project failed")
        return jsonify({"success": False, "error": "更新项目失败"}), 500


@bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    try:
        with SessionLocal() as db:
            try:
                deleted = crud.delete_project(db, project_id, user_id=_project_owner_id())
            except ValueError as exc:
                if str(exc) == "DEFAULT_PROJECT_IMMUTABLE":
                    return jsonify({"success": False, "error": "默认项目不能删除"}), 400
                if str(exc) == "PROJECT_NOT_EMPTY":
                    return jsonify({"success": False, "error": "项目里还有内容，暂时不能删除"}), 400
                raise
            if not deleted:
                return jsonify({"success": False, "error": "项目不存在"}), 404
            return jsonify({"success": True})
    except Exception:
        logger.exception("delete project failed")
        return jsonify({"success": False, "error": "删除项目失败"}), 500
