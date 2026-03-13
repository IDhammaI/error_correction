"""
数据库迁移脚本 — SQLite ALTER TABLE

用法：
    cd backend
    python -m db.migrate
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    if not settings.db_path.exists():
        print(f"[migrate] 数据库文件不存在: {settings.db_path}，跳过迁移")
        return

    conn = sqlite3.connect(str(settings.db_path))
    cursor = conn.cursor()

    migrations = [
        ("questions", "user_answer", "ALTER TABLE questions ADD COLUMN user_answer TEXT"),
        ("questions", "updated_at", "ALTER TABLE questions ADD COLUMN updated_at DATETIME"),
        ("questions", "review_status", "ALTER TABLE questions ADD COLUMN review_status VARCHAR(10) DEFAULT '待复习'"),
    ]

    applied = 0
    for table, column, sql in migrations:
        if _column_exists(cursor, table, column):
            print(f"[migrate] {table}.{column} 已存在，跳过")
        else:
            cursor.execute(sql)
            applied += 1
            print(f"[migrate] 已添加 {table}.{column}")

    # 新建表迁移
    new_tables = [
        ("split_records", """
            CREATE TABLE split_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject VARCHAR(50),
                model_provider VARCHAR(20),
                file_names_json TEXT,
                questions_json TEXT,
                question_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """),
    ]

    for table_name, create_sql in new_tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            print(f"[migrate] 表 {table_name} 已存在，跳过")
        else:
            cursor.execute(create_sql)
            applied += 1
            print(f"[migrate] 已创建表 {table_name}")

    conn.commit()
    conn.close()
    print(f"[migrate] 迁移完成，应用 {applied} 项变更")


if __name__ == "__main__":
    migrate()
