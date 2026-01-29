"""
错题本生成系统 - Web应用
提供前端界面用于测试工作流
"""

import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from src.workflow import build_workflow

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAX_FILE_SIZE_MB = 50
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    处理文件上传并执行预处理

    图执行: prepare_input → ocr_parse → [中断]

    Returns:
        JSON响应，包含处理结果
    """
    # 检查文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'不支持的文件格式。支持: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # 检查文件大小
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小（字节）
    file.seek(0)  # 重置到文件开头
    file_size_mb = file_size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        return jsonify({
            'error': f'文件大小为 {file_size_mb:.1f}MB，超出最大限制 {MAX_FILE_SIZE_MB}MB'
        }), 400

    if file_size == 0:
        return jsonify({
            'error': '上传的文件为空，请重新选择文件'
        }), 400

    try:
        global current_thread_id
        current_thread_id = str(uuid.uuid4())

        # 保存文件（使用uuid生成文件名，支持中文文件名上传）
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{original_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 启动图：prepare_input → ocr_parse → 在 split_questions 前中断
        config = {"configurable": {"thread_id": current_thread_id}}
        state = workflow_graph.invoke({"file_path": filepath}, config=config)

        return jsonify({
            'success': True,
            'message': '文件处理成功',
            'result': {
                'image_count': len(state.get('image_paths', [])),
                'ocr_count': len(state.get('ocr_results', [])),
                'image_paths': state.get('image_paths', []),
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


@app.route('/api/split', methods=['POST'])
def split_questions():
    """
    恢复图执行 Agent 分割题目

    图执行: split_questions → [中断]

    Returns:
        JSON响应，包含分割后的题目
    """
    try:
        global current_thread_id

        if current_thread_id is None:
            return jsonify({
                'success': False,
                'error': '请先上传文件'
            }), 400

        # 恢复图：执行 split_questions → 在 export 前中断
        config = {"configurable": {"thread_id": current_thread_id}}
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
        global current_thread_id

        data = request.get_json()
        selected_ids = data.get('selected_ids', [])

        if not selected_ids:
            return jsonify({
                'success': False,
                'error': '未选择任何题目'
            }), 400

        if current_thread_id is None:
            return jsonify({
                'success': False,
                'error': '请先分割题目'
            }), 400

        config = {"configurable": {"thread_id": current_thread_id}}

        # 将用户选中的题目 ID 注入图状态
        workflow_graph.update_state(config, {"selected_ids": selected_ids})

        # 恢复图：执行 export → END
        state = workflow_graph.invoke(None, config=config)

        return jsonify({
            'success': True,
            'message': '错题本导出成功',
            'output_path': state.get('output_path', '')
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
        results_dir = os.getenv("RESULTS_DIR", "results")
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
    results_dir = os.getenv("RESULTS_DIR", "results")
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
    results_dir = os.getenv("RESULTS_DIR", "results")
    return send_from_directory(results_dir, filename, as_attachment=True)


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
                'pages': os.getenv('PAGES_DIR', 'output/pages'),
                'struct': os.getenv('STRUCT_DIR', 'output/struct'),
                'results': os.getenv('RESULTS_DIR', 'results'),
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
    print("=" * 60)
    print("错题本生成系统 - Web应用")
    print("=" * 60)
    print("访问地址: http://localhost:5001")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
