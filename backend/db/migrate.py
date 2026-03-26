"""
数据库重建脚本 — 清空并重建所有表，创建默认 Admin 用户

用法：
    cd backend
    python -m db.migrate
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from core.config import settings
from db import engine, SessionLocal
from db.models import Base
from db import crud


def migrate():
    """增量迁移：仅创建缺失的表，并确保 Admin 用户存在。每次启动自动调用，安全幂等。"""
    Base.metadata.create_all(bind=engine)  # checkfirst=True by default，已存在的表不动

    default_users = [
        {"email": "admin@admin.com",  "username": "Admin",  "password": "123456", "is_admin": True},
        {"email": "admin2@admin.com", "username": "Admin2", "password": "123456", "is_admin": True},
    ]
    with SessionLocal() as db:
        for u in default_users:
            if not crud.get_user_by_email(db, u["email"]):
                crud.create_user(
                    db,
                    email=u["email"],
                    password_hash=generate_password_hash(u["password"]),
                    username=u["username"],
                    is_admin=u["is_admin"],
                )
                print(f"[migrate] 已创建默认用户: {u['username']} ({u['email']})")


def rebuild():
    """危险：删除所有表并重建。仅用于开发环境手动重置。"""
    print("[migrate] 正在删除所有表...")
    Base.metadata.drop_all(bind=engine)
    print("[migrate] 正在重建所有表...")
    migrate()
    print("[migrate] 重建完成")


if __name__ == "__main__":
    rebuild()
