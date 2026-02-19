"""
错题本生成系统 - Web应用
提供前端界面用于执行工作流
"""

import os
import json
import uuid
import threading
import mimetypes

# Windows 注册表可能将 .js 映射为 text/plain，导致浏览器拒绝加载 ES module
mimetypes.add_type('application/javascript', '.js')
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from dotenv import load_dotenv

from src.workflow import build_workflow
from src.utils import export_wrongbook as export_wrongbook_md
from config import (
    PROJECT_ROOT,
    UPLOAD_DIR,
    PAGES_DIR,
    STRUCT_DIR,
    RESULTS_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
)
from db import init_db

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置（统一从 config.py 导入）
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024


def _safe_join(base_dir: str, rel_path: str) -> str | None:
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, rel_path))
    if os.path.normcase(target).startswith(os.path.normcase(base + os.sep)):
        return target
    return None

@app.errorhandler(413)
def request_entity_too_large(error):
    """文件大小超出Flask限制"""
    return jsonify({
        'success': False,
        'error': f'文件大小超出限制，最大允许 {MAX_FILE_SIZE_MB}MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """页面未找到"""
    return jsonify({
        'success': False,
        'error': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """服务器内部错误"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误，请稍后重试'
    }), 500


# 全局工作流图（带 MemorySaver，通过 thread_id 管理会话状态）
workflow_graph = build_workflow()
current_thread_id = None
session_files = {}
session_file_order = []
cancelled_file_keys = set()
session_lock = threading.Lock()


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return vue_index()


def _vite_manifest():
    manifest_path = os.path.join(PROJECT_ROOT, 'frontend', 'dist', '.vite', 'manifest.json')
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/static/vue/<path:filename>')
def serve_vue_dist(filename):
    dist_dir = os.path.join(PROJECT_ROOT, 'frontend', 'dist')
    return send_from_directory(dist_dir, filename)


def _vite_collect_imports(manifest: dict, entry_key: str):
    seen = set()
    stack = list((manifest.get(entry_key) or {}).get('imports', []))
    out = []
    while stack:
        k = stack.pop()
        if k in seen:
            continue
        seen.add(k)
        item = manifest.get(k)
        if not item:
            continue
        out.append(item['file'])
        stack.extend(item.get('imports', []))
    return out


@app.route('/vue')
def vue_index():
    manifest = _vite_manifest()
    entry_key = 'index.html'
    if not manifest or entry_key not in manifest:
        return render_template('vue.html', vite=None)

    entry = manifest[entry_key]
    base = '/static/vue/'
    vite = {
        'js': f"{base}{entry['file']}",
        'css': [f"{base}{p}" for p in entry.get('css', [])],
        'preload': [f"{base}{p}" for p in _vite_collect_imports(manifest, entry_key)],
    }
    return render_template('vue.html', vite=vite)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传（支持多文件）。

    这里只负责把原始文件保存到 uploads 并登记到会话中；
    标准化(PDF/图片 → 图片列表) + OCR + 分割，会在 /api/split 里由用户点击“开始分割”后统一触发。

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
                'error': f'不支持的文件格式: {file.filename}。支持: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        file_size_mb = file_size / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            return jsonify({
                'error': f'{file.filename} 大小为 {file_size_mb:.1f}MB，超出最大限制 {MAX_FILE_SIZE_MB}MB'
            }), 400

        if file_size == 0:
            return jsonify({
                'error': f'{file.filename} 为空文件，请重新选择'
            }), 400

    try:
        global current_thread_id, session_files, session_file_order

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

            original_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{original_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                if current_thread_id is not None:
                    current_thread_id = None
                    session_files = {}
                    session_file_order = []

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
        return jsonify({
            'success': False,
            'error': f'文件处理失败：{str(e)}'
        }), 500


@app.route('/api/cancel_file', methods=['POST'])
def cancel_file():
    try:
        global current_thread_id, session_files, session_file_order

        data = request.get_json(silent=True) or {}
        file_key = data.get('file_key')
        if not file_key:
            return jsonify({
                'success': False,
                'error': '缺少 file_key'
            }), 400

        if current_thread_id is not None:
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
                session_file_order = [x for x in session_file_order if x != file_key]

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
        return jsonify({
            'success': False,
            'error': f'撤销失败：{str(e)}'
        }), 500


@app.route('/api/split', methods=['POST'])
def split_questions():
    """开始执行标准化 + OCR + 分割。

    用户点击前端“开始分割题目”后调用该接口：
    - 标准化输入（PDF/图片 → 图片列表）
    - 触发 Agent/OCR 并分割题目

    Returns:
        JSON响应，包含分割后的题目
    """
    try:
        global workflow_graph, current_thread_id, session_files, session_file_order

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

        current_thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": current_thread_id}}

        workflow_graph.invoke({"file_paths": file_paths}, config=config)
        state = workflow_graph.invoke(None, config=config)

        questions = state.get('questions', [])

        return jsonify({
            'success': True,
            'message': f'成功分割 {len(questions)} 道题目',
            'questions': questions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'题目分割失败：{str(e)}'
        }), 500


@app.route('/api/export', methods=['POST'])
def export_wrongbook():
    """
    注入选中题目 ID 并恢复图执行导出

    图执行: export → END

    Returns:
        JSON响应，包含导出文件路径
    """
    try:
        global current_thread_id, session_files, session_file_order

        data = request.get_json()
        selected_ids = data.get('selected_ids', [])
        subject = data.get('subject')  # 前端传入科目（可选）

        if not selected_ids:
            return jsonify({
                'success': False,
                'error': '未选择任何题目'
            }), 400

        # 检查是否已分割（通过 questions.json 存在性判断，不依赖内存中的 current_thread_id）
        results_dir = RESULTS_DIR
        questions_file = os.path.join(results_dir, "questions.json")
        if not os.path.exists(questions_file):
            return jsonify({
                'success': False,
                'error': '请先分割题目'
            }), 400

        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        # 构建批次信息用于入库
        batch_info = {
            "original_filename": ", ".join(
                session_files.get(k, {}).get("filename", "未知")
                for k in session_file_order
            ),
            "subject": subject,
            "file_path": "",
        }

        output_path = export_wrongbook_md(
            questions,
            selected_ids,
            batch_info=batch_info
        )

        return jsonify({
            'success': True,
            'message': '错题本导出成功',
            'output_path': output_path
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出失败：{str(e)}'
        }), 500


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """
    获取已分割的题目列表

    Returns:
        JSON响应，包含题目列表
    """
    try:
        results_dir = RESULTS_DIR
        questions_file = os.path.join(results_dir, "questions.json")

        if not os.path.exists(questions_file):
            return jsonify({
                'success': True,
                'questions': [],
                'message': '暂无题目数据'
            })

        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        return jsonify({
            'success': True,
            'questions': questions
        })

    except json.JSONDecodeError:
        return jsonify({
            'success': False,
            'error': '题目数据文件格式错误，请重新分割题目'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取题目列表失败：{str(e)}'
        }), 500


@app.route('/preview')
def preview():
    """显示预览页面"""
    results_dir = RESULTS_DIR
    preview_file = os.path.join(results_dir, "preview.html")

    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    else:
        return "预览文件不存在，请先分割题目", 404


@app.route('/download/<path:filename>')
def download_file(filename):
    """下载结果文件"""
    results_dir = RESULTS_DIR
    file_path = _safe_join(results_dir, filename)
    if not file_path:
        return jsonify({
            'success': False,
            'error': '非法文件路径'
        }), 400

    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'error': '文件不存在'
        }), 404

    resp = send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(filename),
        conditional=False,
        etag=False,
        max_age=0,
    )
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供 OCR 解析出的图片资源"""
    return send_from_directory(os.path.join(STRUCT_DIR, "imgs"), filename)


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    获取系统状态

    Returns:
        JSON响应，包含系统配置和状态
    """
    try:
        # 检查配置
        status = {
            'paddleocr_configured': bool(os.getenv('PADDLEOCR_API_URL')),
            'deepseek_configured': bool(os.getenv('DEEPSEEK_API_KEY')),
            'langsmith_enabled': os.getenv('LANGSMITH_TRACING', 'false').lower() == 'true',
            'output_dirs': {
                'pages': PAGES_DIR,
                'struct': STRUCT_DIR,
                'results': RESULTS_DIR,
            }
        }

        return jsonify({
            'success': True,
            'status': status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取系统状态失败：{str(e)}'
        }), 500


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("[数据库] 初始化完成")

    print("=" * 60)
    print("错题本生成系统 - Web应用")
    print("=" * 60)
    print("访问地址: http://localhost:5001")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
