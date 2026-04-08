"""
全局会话状态 — 供各 Blueprint 模块共享

所有需要跨路由访问的运行时变量集中在此模块，
通过 session_lock 保护并发写操作。
"""

import threading

from src.workflow import build_workflow

# 全局工作流图（带 MemorySaver，通过 thread_id 管理会话状态）
workflow_graph = build_workflow()
current_thread_id = None

# 上传会话状态
session_files = {}          # file_key → {filename, filepath}
session_file_order = []     # 上传顺序
cancelled_file_keys = set() # 已取消的文件 key
erased_file_paths = None    # 擦除后的文件路径列表（由 /api/erase 写入，/api/ocr 消费）

# 线程锁
session_lock = threading.Lock()
