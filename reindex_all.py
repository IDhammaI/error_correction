
import sys
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

# 将 backend 目录加入路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from db import SessionLocal
from db.models import Question
from core.rag import index_question

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def reindex_all():
    """为数据库中所有现有的题目重建 RAG 索引"""
    logger.info("开始为所有现有题目重建 RAG 索引...")
    
    with SessionLocal() as db:
        # 获取所有题目
        questions = db.query(Question).all()
        total = len(questions)
        logger.info(f"找到 {total} 道题目需要处理")
        
        success_count = 0
        fail_count = 0
        
        for i, q in enumerate(questions):
            try:
                # 传入 db session 处理单道题目
                # index_question 内部会处理向量生成和数据库写入
                if index_question(db, q.id):
                    success_count += 1
                else:
                    fail_count += 1
                
                if (i + 1) % 5 == 0 or (i + 1) == total:
                    logger.info(f"进度: {i + 1}/{total} (成功: {success_count}, 失败: {fail_count})")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"索引题目 ID={q.id} 时发生错误: {e}")

    logger.info(f"索引重建完成！成功: {success_count}, 失败: {fail_count}")

if __name__ == "__main__":
    reindex_all()
