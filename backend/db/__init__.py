"""
数据库模块：引擎创建、Session 工厂、初始化函数
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
import sys

# 添加 backend 目录到路径以支持导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

# 确保数据库目录存在
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# 创建引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 启用 SQLite 外键约束
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """应用启动时调用：建表"""
    from db.models import Base
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话（用于手动管理）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
