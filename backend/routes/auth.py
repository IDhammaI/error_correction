from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import SessionLocal
from db import crud

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def auth_register():
    """用户注册"""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not email or '@' not in email:
        return jsonify({'error': '邮箱格式不正确'}), 400
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码至少 6 位'}), 400

    with SessionLocal() as db:
        if crud.get_user_by_email(db, email):
            return jsonify({'error': '该邮箱已注册'}), 409
        pwd_hash = generate_password_hash(password)
        user = crud.create_user(db, email=email, password_hash=pwd_hash, username=username)
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'user': {'id': user.id, 'email': user.email, 'username': user.username, 'is_admin': user.is_admin}}), 201


@bp.route('/login', methods=['POST'])
def auth_login():
    """用户登录（支持邮箱或用户名）"""
    data = request.get_json() or {}
    identifier = (data.get('email') or data.get('identifier') or '').strip()
    password = data.get('password') or ''

    if not identifier:
        return jsonify({'error': '请输入邮箱或用户名'}), 400

    with SessionLocal() as db:
        user = crud.get_user_by_login(db, identifier)
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': '账号或密码错误'}), 401
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'user': {'id': user.id, 'email': user.email, 'username': user.username, 'is_admin': user.is_admin}})


@bp.route('/logout', methods=['POST'])
def auth_logout():
    """退出登录"""
    session.clear()
    return jsonify({'ok': True})


@bp.route('/me', methods=['GET'])
def auth_me():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登录', 'code': 'UNAUTHORIZED'}), 401
    with SessionLocal() as db:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            session.clear()
            return jsonify({'error': '用户不存在', 'code': 'UNAUTHORIZED'}), 401
        return jsonify({'user': {'id': user.id, 'email': user.email, 'username': user.username, 'is_admin': user.is_admin}})
