"""
错题本生成系统 - Web应用（纯 API 服务）
"""

import os
import logging

from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from dotenv import load_dotenv

from config import settings
from db import init_db, SessionLocal
from routes import register_routes

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')

# 跨域支持（前端 dev server 端口不同）
CORS(app, supports_credentials=True)

# 配置
app.config['UPLOAD_FOLDER'] = settings.upload_dir
app.config['MAX_CONTENT_LENGTH'] = settings.max_file_size_mb * 1024 * 1024


# ============================================================
# 全局错误处理
# ============================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': f'文件大小超出限制，最大允许 {settings.max_file_size_mb}MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误，请稍后重试'
    }), 500


# ============================================================
# 全局中间件
# ============================================================

@app.before_request
def require_login():
    """所有 /api/ 路由（除 /api/auth/ 和 /api/status）要求登录"""
    if request.path.startswith('/api/'):
        if request.path.startswith('/api/auth/') or request.path == '/api/status':
            return None
        if 'user_id' not in session:
            return jsonify({'error': '请先登录', 'code': 'UNAUTHORIZED'}), 401
    return None


# ============================================================
# 注册 Blueprint 路由
# ============================================================

register_routes(app)


# ============================================================
# 静态资源服务（OCR 图片、下载、擦除结果）
# ============================================================

def _safe_join(base_dir: str, rel_path: str) -> str | None:
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, rel_path))
    if os.path.normcase(target).startswith(os.path.normcase(base + os.sep)):
        return target
    return None


@app.route('/download/<path:filename>')
def download_file(filename):
    """下载结果文件"""
    file_path = _safe_join(settings.results_dir, filename)
    if not file_path:
        return jsonify({'success': False, 'error': '非法文件路径'}), 400
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '文件不存在'}), 404

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
    base = os.path.join(settings.struct_dir, "imgs")
    file_path = _safe_join(base, filename)
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '图片不存在'}), 404
    return send_file(file_path)


@app.route('/erased/<path:filename>')
def serve_erased_image(filename):
    """提供擦除结果图片"""
    file_path = _safe_join(str(settings.erased_dir), filename)
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '图片不存在'}), 404
    return send_file(file_path)


# ============================================================
# 启动入口
# ============================================================

if __name__ == '__main__':
    settings.ensure_dirs()
    init_db()
    from db.migrate import migrate
    migrate()
    print("[数据库] 初始化完成")

    print("=" * 60)
    print("错题本生成系统 - API 服务")
    print("=" * 60)
    print("API 地址: http://localhost:5001")
    print("前端开发: cd frontend && npm run dev")
    print("=" * 60)

    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(
        host='0.0.0.0', port=5001, debug=debug,
        exclude_patterns=["*site-packages*"],
    )
