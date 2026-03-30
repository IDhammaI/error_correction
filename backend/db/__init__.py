"""
数据库模块：引擎创建、Session 工厂、初始化函数
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
import sys

# 添加 backend 目录到路径以支持导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import settings

# 确保数据库目录存在
db_dir = settings.db_path.parent
db_dir.mkdir(parents=True, exist_ok=True)

# 创建引擎
engine = create_engine(f"sqlite:///{settings.db_path}", echo=False)

# 启用 SQLite 外键约束
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_schema():
    """轻量级自动迁移：为已有表补充新列"""
    import sqlite3
    conn = sqlite3.connect(str(settings.db_path))
    try:
        cursor = conn.cursor()
        # 检查 questions 表是否有 answer 列
        cursor.execute("PRAGMA table_info(questions)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'answer' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN answer TEXT")
            conn.commit()

        # chat_sessions 表：question_id 需要改为 nullable
        # SQLite 不支持 ALTER COLUMN，需要重建表
        cursor.execute("PRAGMA table_info(chat_sessions)")
        cs_columns = {row[1]: row for row in cursor.fetchall()}
        if 'title' not in cs_columns:
            # 旧表结构，需要重建
            cursor.execute("DROP TABLE IF EXISTS chat_messages")
            cursor.execute("DROP TABLE IF EXISTS chat_sessions")
            conn.commit()
    finally:
        conn.close()


def init_db():
    """应用启动时调用：建表 + 迁移"""
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    _migrate_schema()


def get_db():
    """获取数据库会话（用于手动管理）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
