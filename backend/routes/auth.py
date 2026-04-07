import hmac
import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from core.config import settings
from core.mail import send_smtp_email
from db import SessionLocal
from db import crud

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


def _hash_registration_code(email: str, code: str, pepper: str) -> str:
    raw = f"{email.lower().strip()}:{code}".encode("utf-8")
    return hmac.new(pepper.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def _generate_six_digit_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


@bp.route("/register", methods=["POST"])
def auth_register():
    """用户注册（需先调用 /send-code?type=register 并填写正确验证码）。"""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    code = (data.get("code") or "").strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "邮箱格式不正确"}), 400
    if not username:
        return jsonify({"success": False, "error": "用户名不能为空"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "密码至少 6 位"}), 400
    if not code or not code.isdigit() or len(code) != 6:
        return jsonify({"success": False, "error": "请输入 6 位邮箱验证码"}), 400

    pepper = (current_app.secret_key or "dev-secret-change-in-production")[:64]
    submitted_hash = _hash_registration_code(email, code, pepper)
    now = datetime.utcnow()

    user_id = None
    username_out = None
    email_out = None
    is_admin_out = None

    with SessionLocal() as db:
        if crud.get_user_by_email(db, email):
            return jsonify({"success": False, "error": "该邮箱已注册"}), 409

        row = crud.get_verification_by_email(db, email)
        if not row:
            return jsonify({"success": False, "error": "请先获取邮箱验证码"}), 400
        if row.expires_at < now:
            crud.delete_verification_by_email(db, email)
            return jsonify({"success": False, "error": "验证码已过期，请重新获取"}), 400
        if (row.attempts or 0) >= settings.registration_max_attempts:
            crud.delete_verification_by_email(db, email)
            return jsonify({"success": False, "error": "验证失败次数过多，请重新获取验证码"}), 400

        if not hmac.compare_digest(row.code_hash, submitted_hash):
            crud.increment_verification_attempts(db, email)
            return jsonify({"success": False, "error": "验证码错误"}), 400

        pwd_hash = generate_password_hash(password)
        user = crud.create_user(db, email=email, password_hash=pwd_hash, username=username)
        crud.delete_verification_by_email(db, email)
        # 将需要的字段提前取出为纯 Python 变量，避免脱离 Session 后访问 ORM 对象触发 DetachedInstanceError
        user_id = user.id
        username_out = user.username
        email_out = user.email
        is_admin_out = user.is_admin

    session["user_id"] = user_id
    session["username"] = username_out
    session["session_version"] = 0
    return jsonify(
        {
            "success": True,
            "user": {
                "id": user_id,
                "email": email_out,
                "username": username_out,
                "is_admin": is_admin_out,
            },
        }
    ), 201


@bp.route("/send-code", methods=["POST"])
def send_code():
    """发送验证码（支持注册和找回密码两种场景）。

    请求体：{ email, type: 'register' | 'reset' }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code_type = (data.get("type") or "register").strip().lower()

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "邮箱格式不正确"}), 400

    now = datetime.utcnow()
    with SessionLocal() as db:
        user = crud.get_user_by_email(db, email)
        # 防邮箱枚举：注册时邮箱已存在、重置时邮箱不存在，均返回相同成功响应但不实际发送
        if (code_type == "register" and user) or (code_type == "reset" and not user):
            return jsonify({"success": True, "message": "验证码已发送"})

        row = crud.get_verification_by_email(db, email)
        if row and row.last_sent_at:
            delta = (now - row.last_sent_at).total_seconds()
            if delta < settings.registration_send_interval_seconds:
                wait = int(settings.registration_send_interval_seconds - delta)
                return jsonify(
                    {"success": False, "error": f"发送过于频繁，请 {wait} 秒后再试"}
                ), 429

    code = _generate_six_digit_code()
    pepper = (current_app.secret_key or "dev-secret-change-in-production")[:64]
    code_hash = _hash_registration_code(email, code, pepper)
    expires_at = now + timedelta(minutes=settings.registration_code_ttl_minutes)

    with SessionLocal() as db:
        crud.upsert_registration_code(db, email, code_hash, expires_at, now)

    subject_text = "找回密码" if code_type == "reset" else "注册"
    smtp_ok = bool(settings.smtp_host and settings.smtp_from)
    if smtp_ok:
        try:
            send_smtp_email(
                host=settings.smtp_host,
                port=settings.smtp_port,
                user=settings.smtp_user,
                password=settings.smtp_password,
                mail_from=settings.smtp_from,
                use_tls=settings.smtp_use_tls,
                to_addr=email,
                subject=f"【智卷系统】{subject_text}验证码",
                body=f"您的{subject_text}验证码为：{code}，{settings.registration_code_ttl_minutes} 分钟内有效。请勿泄露给他人。",
            )
        except Exception as e:
            logger.exception("发送验证码邮件失败")
            return jsonify({"success": False, "error": f"邮件发送失败：{e!s}"}), 502
    else:
        if current_app.debug:
            logger.warning(
                "[开发模式] 未配置 SMTP，验证码（仅调试用） email=%s code=%s",
                email,
                code,
            )
        else:
            return jsonify(
                {"success": False, "error": "服务器未配置发信，无法发送验证码"}
            ), 503

    return jsonify({"success": True, "message": "验证码已发送"})


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    """通过邮箱验证码重置密码。

    请求体：{ email, code, password }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    password = data.get("password") or ""

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "邮箱格式不正确"}), 400
    if not code or not code.isdigit() or len(code) != 6:
        return jsonify({"success": False, "error": "请输入 6 位验证码"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "密码至少 6 位"}), 400

    pepper = (current_app.secret_key or "dev-secret-change-in-production")[:64]
    submitted_hash = _hash_registration_code(email, code, pepper)
    now = datetime.utcnow()

    with SessionLocal() as db:
        user = crud.get_user_by_email(db, email)
        if not user:
            return jsonify({"success": False, "error": "该邮箱未注册"}), 404

        row = crud.get_verification_by_email(db, email)
        if not row:
            return jsonify({"success": False, "error": "请先获取验证码"}), 400
        if row.expires_at < now:
            crud.delete_verification_by_email(db, email)
            return jsonify({"success": False, "error": "验证码已过期，请重新获取"}), 400
        if (row.attempts or 0) >= settings.registration_max_attempts:
            crud.delete_verification_by_email(db, email)
            return jsonify({"success": False, "error": "验证失败次数过多，请重新获取验证码"}), 400

        if not hmac.compare_digest(row.code_hash, submitted_hash):
            crud.increment_verification_attempts(db, email)
            return jsonify({"success": False, "error": "验证码错误"}), 400

        if check_password_hash(user.password_hash, password):
            return jsonify({"success": False, "error": "新密码不能与原密码相同"}), 400

        new_hash = generate_password_hash(password)
        crud.update_user_password(db, email, new_hash)
        crud.delete_verification_by_email(db, email)

    return jsonify({"success": True, "message": "密码重置成功"})


@bp.route("/login", methods=["POST"])
def auth_login():
    """用户登录（支持邮箱或用户名）"""
    data = request.get_json() or {}
    identifier = (data.get("email") or data.get("identifier") or "").strip()
    password = data.get("password") or ""

    if not identifier:
        return jsonify({"error": "请输入邮箱或用户名"}), 400

    with SessionLocal() as db:
        user = crud.get_user_by_login(db, identifier)
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "账号或密码错误"}), 401
        session["user_id"] = user.id
        session["username"] = user.username
        session["session_version"] = user.session_version or 0
        return jsonify(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_admin": user.is_admin,
                }
            }
        )


@bp.route("/logout", methods=["POST"])
def auth_logout():
    """退出登录"""
    session.clear()
    return jsonify({"ok": True})


@bp.route("/me", methods=["GET"])
def auth_me():
    """获取当前登录用户"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录", "code": "UNAUTHORIZED"}), 401
    with SessionLocal() as db:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            session.clear()
            return jsonify({"error": "用户不存在", "code": "UNAUTHORIZED"}), 401
        return jsonify(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_admin": user.is_admin,
                }
            }
        )
