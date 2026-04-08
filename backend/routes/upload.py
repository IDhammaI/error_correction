import os
import json
import uuid
import logging
from pathlib import PurePath
from typing import Optional

from flask import Blueprint, request, jsonify, session

import core.state as state
from core.state import (
    workflow_graph,
    session_files,
    session_file_order,
    cancelled_file_keys,
    session_lock,
)
from db import SessionLocal
from db import crud
from core.config import settings
from src.utils import export_wrongbook as export_wrongbook_md

logger = logging.getLogger(__name__)

bp = Blueprint('upload', __name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return PurePath(filename).suffix.lower().lstrip('.') in settings.allowed_extensions


def _read_split_subject() -> Optional[str]:
    """从 split_metadata.json 读取学科信息"""
    meta_path = os.path.join(str(settings.results_dir), "split_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("subject")
    return None


def _serialize_split_record(r) -> dict:
    """将 SplitRecord ORM 对象序列化为前端 JSON 格式"""
    return {
        "id": r.id,
        "subject": r.subject,
        "model_provider": r.model_provider,
        "file_names": json.loads(r.file_names_json) if r.file_names_json else [],
        "question_count": r.question_count,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传（支持多文件）。

    这里只负责把原始文件保存到 uploads 并登记到会话中；
    标准化(PDF/图片 → 图片列表) + OCR + 分割，会在 /api/split 里由用户点击"开始分割"后统一触发。

    Returns:
        JSON响应，包含上传结果
    """
    # 支持多文件：前端用 'files' 字段发送，兼容单文件 'file' 字段
    files = request.files.getlist('files')
    if not files:
        files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '没有上传文件'}), 400

    # 校验每个文件
    for file in files:
        if file.filename == '':
            continue

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'不支持的文件格式: {file.filename}。支持: {", ".join(settings.allowed_extensions)}'
            }), 400

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        file_size_mb = file_size / (1024 * 1024)

        if file_size_mb > settings.max_file_size_mb:
            return jsonify({
                'error': f'{file.filename} 大小为 {file_size_mb:.1f}MB，超出最大限制 {settings.max_file_size_mb}MB'
            }), 400

        if file_size == 0:
            return jsonify({
                'error': f'{file.filename} 为空文件，请重新选择'
            }), 400

    try:
        file_keys = request.form.getlist('file_key')
        if not file_keys:
            file_keys = request.form.getlist('file_keys')

        prepared = []
        for i, file in enumerate(files):
            if file.filename == '':
                continue
            fk = file_keys[i] if i < len(file_keys) and file_keys[i] else None
            prepared.append((fk, file))

        if not prepared:
            return jsonify({'error': '没有上传文件'}), 400

        results_out = []
        for fk, file in prepared:
            file_key = fk or f"{uuid.uuid4().hex}"

            original_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            filename = f"{uuid.uuid4().hex}.{original_ext}"
            filepath = os.path.join(str(settings.upload_dir), filename)
            file.save(filepath)

            with session_lock:
                cancelled = file_key in cancelled_file_keys
                if cancelled:
                    cancelled_file_keys.discard(file_key)

            if cancelled:
                try:
                    os.remove(filepath)
                except FileNotFoundError:
                    pass
                continue

            with session_lock:
                if state.current_thread_id is not None:
                    state.current_thread_id = None
                    state.session_files.clear()
                    state.session_file_order.clear()

                session_files[file_key] = {
                    "filename": file.filename,
                    "filepath": filepath,
                }
                if file_key not in session_file_order:
                    session_file_order.append(file_key)

            results_out.append({
                "file_key": file_key,
                "filename": file.filename,
            })

        return jsonify({
            'success': True,
            'message': '上传成功',
            'result': {
                'file_count': len(results_out),
                'files': results_out,
            }
        })

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': '文件保存失败，请重新上传'
        }), 500
    except Exception as e:
        logger.exception("文件处理失败")
        return jsonify({
            'success': False,
            'error': '文件处理失败，请稍后重试'
        }), 500


@bp.route('/cancel_file', methods=['POST'])
def cancel_file():
    try:
        data = request.get_json(silent=True) or {}
        file_key = data.get('file_key')
        if not file_key:
            return jsonify({
                'success': False,
                'error': '缺少 file_key'
            }), 400

        if state.current_thread_id is not None:
            return jsonify({
                'success': False,
                'error': '已开始分割，无法撤销单个文件；请重置后重新上传'
            }), 400

        filepath = None
        existed = False
        with session_lock:
            cancelled_file_keys.add(file_key)

            existed = file_key in session_files
            v = session_files.pop(file_key, None) or {}
            filepath = v.get('filepath')
            if file_key in session_file_order:
                session_file_order.remove(file_key)

            cancelled_file_keys.discard(file_key)

        if filepath:
            try:
                os.remove(filepath)
            except FileNotFoundError:
                pass

        return jsonify({
            'success': True,
            'message': '已撤销该文件' if existed else '已标记撤销该文件',
        })

    except Exception as e:
        logger.exception("撤销文件失败")
        return jsonify({
            'success': False,
            'error': '撤销失败，请稍后重试'
        }), 500


@bp.route('/ocr', methods=['POST'])
def run_ocr():
    """只执行 OCR，返回识别结果供用户预览。

    流程：标准化输入 → OCR 解析 → 返回结构化文本
    不触发 Agent 分割。
    """
    try:
        data = request.get_json(silent=True) or {}
        erase = data.get("erase", True)

        # 加载 OCR 凭据
        user_id = session.get('user_id')
        ocr_credentials = {}
        if user_id:
            with SessionLocal() as db:
                ocr_provider = crud.get_active_provider(db, user_id, 'paddleocr')
                if ocr_provider:
                    ocr_credentials = {
                        "api_url": ocr_provider.base_url,
                        "token": ocr_provider.api_key,
                        "model": ocr_provider.model_name,
                        "use_doc_orientation": ocr_provider.use_doc_orientation,
                        "use_doc_unwarping": ocr_provider.use_doc_unwarping,
                        "use_chart_recognition": ocr_provider.use_chart_recognition,
                    }

        with session_lock:
            keys = list(session_file_order)
            file_paths = []
            for k in keys:
                v = session_files.get(k) or {}
                fp = v.get('filepath')
                if fp:
                    file_paths.append(fp)

        if not file_paths:
            return jsonify({'success': False, 'error': '请先上传文件'}), 400

        # 擦除手写字迹
        ensexam_configured = settings.model_path.exists()
        if ensexam_configured and erase:
            try:
                from models.inference import InferenceEngine
                engine = InferenceEngine()
                erased_paths = []
                for fp in file_paths:
                    with open(fp, 'rb') as f:
                        img_bytes = f.read()
                    result_img = engine.run(img_bytes)
                    erased_name = f"auto_{uuid.uuid4().hex[:8]}_{os.path.basename(fp)}"
                    if not erased_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        erased_name += '.png'
                    erased_path = settings.erased_dir / erased_name
                    result_img.save(str(erased_path), format='PNG')
                    erased_paths.append(str(erased_path))
                file_paths = erased_paths
            except Exception:
                logger.exception("自动擦除手写字迹失败，使用原图继续")

        # 标准化输入（PDF → 图片）
        from src.utils import prepare_input
        all_image_paths = []
        for fp in file_paths:
            all_image_paths.extend(prepare_input(fp))

        # 执行 OCR
        from src.workflow import _run_ocr_and_simplify
        ocr_data = _run_ocr_and_simplify(all_image_paths, ocr_credentials=ocr_credentials)

        if not ocr_data:
            return jsonify({'success': False, 'error': 'OCR 解析失败，请检查 PaddleOCR 配置'}), 500

        # 保存 OCR 结果到会话，供后续 /api/split 复用
        import json
        results_dir = str(settings.results_dir)
        os.makedirs(results_dir, exist_ok=True)
        ocr_cache_path = os.path.join(results_dir, "ocr_cache.json")
        with open(ocr_cache_path, 'w', encoding='utf-8') as f:
            json.dump(ocr_data, f, ensure_ascii=False, indent=2)

        # 构建前端预览数据：每页的 OCR 文本 + 对应的图片路径
        preview_pages = []
        for i, page in enumerate(ocr_data):
            blocks = page.get("blocks", [])
            text = "\n".join(b.get("text", "") for b in blocks if b.get("text"))
            image_path = all_image_paths[i] if i < len(all_image_paths) else None
            # 转为可访问的 URL
            image_url = None
            if image_path:
                image_url = f"/api/upload/image/{os.path.basename(image_path)}"
            preview_pages.append({
                "page_index": i,
                "text": text,
                "block_count": len(blocks),
                "image_url": image_url,
            })

        return jsonify({
            'success': True,
            'message': f'OCR 完成，共 {len(ocr_data)} 页',
            'pages': preview_pages,
            'total_blocks': sum(len(p.get("blocks", [])) for p in ocr_data),
        })

    except Exception:
        logger.exception("OCR 执行失败")
        return jsonify({'success': False, 'error': 'OCR 执行失败，请稍后重试'}), 500


@bp.route('/split', methods=['POST'])
def split_questions():
    """开始执行标准化 + OCR + 分割。

    用户点击前端"开始分割题目"后调用该接口：
    - 标准化输入（PDF/图片 → 图片列表）
    - 触发 Agent/OCR 并分割题目

    Returns:
        JSON响应，包含分割后的题目
    """
    try:
        # 读取请求体参数（模型供应商 + 模型名称）
        data = request.get_json(silent=True) or {}
        model_provider = data.get("model_provider", "openai")
        model_name = data.get("model_name")  # 可选，None 时使用 provider 默认模型
        if not settings.is_valid_provider(model_provider):
            return jsonify({
                'success': False,
                'error': f'不支持的模型供应商: {model_provider}'
            }), 400

        # 从数据库加载用户的 LLM + OCR 凭据
        user_id = session.get('user_id')
        ocr_credentials = {}
        if user_id:
            settings.load_providers_from_db(user_id)
            with SessionLocal() as db:
                ocr_provider = crud.get_active_provider(db, user_id, 'paddleocr')
                if ocr_provider:
                    ocr_credentials = {
                        "api_url": ocr_provider.base_url,
                        "token": ocr_provider.api_key,
                        "model": ocr_provider.model_name,
                        "use_doc_orientation": ocr_provider.use_doc_orientation,
                        "use_doc_unwarping": ocr_provider.use_doc_unwarping,
                        "use_chart_recognition": ocr_provider.use_chart_recognition,
                    }

        with session_lock:
            keys = list(session_file_order)
            file_paths = []
            for k in keys:
                v = session_files.get(k) or {}
                fp = v.get('filepath')
                if fp:
                    file_paths.append(fp)

        if not file_paths:
            return jsonify({
                'success': False,
                'error': '请先上传文件'
            }), 400

        # 擦除手写字迹（EnsExam 已接入且前端未关闭擦除开关时执行）
        erase = data.get("erase", True)
        ensexam_configured = settings.model_path.exists()
        if ensexam_configured and erase:
            try:
                from models.inference import InferenceEngine
                engine = InferenceEngine()
                erased_paths = []
                for fp in file_paths:
                    # 如果是 PDF 转换为图片的临时路径，或者是直接上传的图片
                    with open(fp, 'rb') as f:
                        img_bytes = f.read()
                    result_img = engine.run(img_bytes)

                    # 生成擦除后的文件名，保存在 erased_dir
                    erased_name = f"auto_{uuid.uuid4().hex[:8]}_{os.path.basename(fp)}"
                    if not erased_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        erased_name += '.png'

                    erased_path = settings.erased_dir / erased_name
                    result_img.save(str(erased_path), format='PNG')
                    erased_paths.append(str(erased_path))

                file_paths = erased_paths
                logger.info("EnsExam 已接入，自动擦除 %d 张图片的手写字迹", len(erased_paths))
            except Exception:
                logger.exception("自动擦除手写字迹失败，使用原图继续流程")

        state.current_thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": state.current_thread_id}}

        initial_state = {
            "file_paths": file_paths,
            "model_provider": model_provider,
            "model_name": model_name,
            "ocr_credentials": ocr_credentials,
        }
        workflow_graph.invoke(initial_state, config=config)
        result_state = workflow_graph.invoke(None, config=config)

        questions = result_state.get('questions', [])
        warnings = result_state.get('warnings', [])

        # 自动保存分割记录
        try:
            subject = _read_split_subject()

            with session_lock:
                file_names = [
                    session_files.get(k, {}).get("filename", "未知")
                    for k in session_file_order
                ]

            with SessionLocal() as db:
                crud.save_split_record(db, subject, model_provider, file_names, questions, user_id=session.get('user_id'))
        except Exception:
            logger.warning("保存分割记录失败，不影响主流程", exc_info=True)

        return jsonify({
            'success': True,
            'message': f'成功分割 {len(questions)} 道题目',
            'questions': questions,
            'warnings': warnings,
        })

    except Exception as e:
        logger.exception("题目分割失败")
        return jsonify({
            'success': False,
            'error': '题目分割失败，请稍后重试'
        }), 500


@bp.route('/split-records', methods=['GET'])
def get_split_records():
    """获取最近 N 次分割历史记录，limit 由前端通过查询参数指定"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = max(1, min(limit, crud.MAX_SPLIT_RECORDS))  # 上限与保留条数一致

        with SessionLocal() as db:
            records = crud.get_recent_split_records(db, limit, user_id=session.get('user_id'))
            result = [_serialize_split_record(r) for r in records]

        return jsonify({"success": True, "records": result})

    except Exception as e:
        logger.exception("获取分割记录失败")
        return jsonify({"success": False, "error": "获取分割记录失败"}), 500


@bp.route('/split-records/<int:record_id>', methods=['GET'])
def get_split_record_detail(record_id):
    """获取单条分割记录的完整数据（含 questions）"""
    try:
        with SessionLocal() as db:
            record = crud.get_split_record_by_id(db, record_id)
            if not record:
                return jsonify({"success": False, "error": "记录不存在"}), 404

            result = _serialize_split_record(record)
            result["questions"] = json.loads(record.questions_json) if record.questions_json else []

        return jsonify({"success": True, "record": result})

    except Exception as e:
        logger.exception("获取分割记录详情失败")
        return jsonify({"success": False, "error": "获取分割记录详情失败"}), 500


@bp.route('/export', methods=['POST'])
def export_wrongbook():
    """
    注入选中题目 ID 并恢复图执行导出

    图执行: export → END

    Returns:
        JSON响应，包含导出文件路径
    """
    try:
        data = request.get_json(silent=True) or {}
        selected_ids = data.get('selected_ids', [])

        if not isinstance(selected_ids, list):
            return jsonify({
                'success': False,
                'error': 'selected_ids 必须为列表'
            }), 400

        if not selected_ids:
            return jsonify({
                'success': False,
                'error': '未选择任何题目'
            }), 400

        # 检查是否已分割（通过 questions.json 存在性判断，不依赖内存中的 current_thread_id）
        results_dir = settings.results_dir
        questions_file = os.path.join(results_dir, "questions.json")
        if not os.path.exists(questions_file):
            return jsonify({
                'success': False,
                'error': '请先分割题目'
            }), 400

        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        output_path = export_wrongbook_md(
            questions,
            selected_ids,
        )

        return jsonify({
            'success': True,
            'message': '错题本导出成功',
            'output_path': output_path
        })

    except Exception as e:
        logger.exception("导出失败")
        return jsonify({
            'success': False,
            'error': '导出失败，请稍后重试'
        }), 500


@bp.route('/image/<filename>')
def serve_image(filename):
    """提供上传/处理后的图片文件访问（OCR 预览用）"""
    from flask import send_from_directory
    # 在多个目录中查找
    for d in [settings.upload_dir, settings.erased_dir, settings.results_dir]:
        path = os.path.join(str(d), filename)
        if os.path.exists(path):
            return send_from_directory(str(d), filename)
    return jsonify({'error': 'File not found'}), 404
