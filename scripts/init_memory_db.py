#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二大脑记忆系统 - 数据库初始化脚本
运行此脚本创建所有必要的数据库表结构
"""

import os
import sys
import sqlite3
from datetime import datetime

# 配置路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'memory_db')

def create_directories():
    """创建必要的目录"""
    os.makedirs(DB_DIR, exist_ok=True)
    print(f"数据库目录: {DB_DIR}")

def create_memories_table(conn):
    """创建记忆库表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            agent_id TEXT,
            content TEXT NOT NULL,
            text_summary TEXT,
            tags TEXT,
            importance TEXT DEFAULT 'medium',
            archive_level TEXT DEFAULT 'hot',
            is_stamped INTEGER DEFAULT 0,
            query_freq INTEGER DEFAULT 0,
            weight REAL DEFAULT 1.0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_archive ON memories(archive_level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)')
    print("  memories 表创建成功")

def create_knowledge_table(conn):
    """创建知识库表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            content TEXT NOT NULL,
            topic TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    # 创建FTS虚拟表
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            title, description, content, content=knowledge
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge(topic)')
    print("  knowledge 表创建成功")

def create_permissions_table(conn):
    """创建权限表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            knowledge_id TEXT NOT NULL,
            permission TEXT DEFAULT 'read',
            created_at TEXT,
            UNIQUE(agent_id, knowledge_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_agent ON permissions(agent_id)')
    print("  permissions 表创建成功")

def create_retrieval_logs_table(conn):
    """创建检索日志表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS retrieval_logs (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            returned_summary TEXT,
            quality_score REAL,
            user_feedback TEXT,
            cleaned INTEGER DEFAULT 0,
            case_type TEXT,
            user_id TEXT,
            agent_id TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_user ON retrieval_logs(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_cleaned ON retrieval_logs(cleaned)')
    print("  retrieval_logs 表创建成功")

def create_user_preferences_table(conn):
    """创建用户偏好表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            query_habit TEXT,
            preferred_domain TEXT,
            active_hours TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    print("  user_preferences 表创建成功")

def create_announcements_table(conn):
    """创建公告表"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    print("  announcements 表创建成功")

def init_database():
    """初始化数据库"""
    print("=" * 50)
    print("第二大脑记忆系统 - 数据库初始化")
    print("=" * 50)
    
    # 创建目录
    create_directories()
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    print(f"数据库文件: {DB_PATH}")
    
    try:
        # 创建所有表
        print("\n创建数据表...")
        create_memories_table(conn)
        create_knowledge_table(conn)
        create_permissions_table(conn)
        create_retrieval_logs_table(conn)
        create_user_preferences_table(conn)
        create_announcements_table(conn)
        
        # 提交更改
        conn.commit()
        
        # 验证
        print("\n验证表结构...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"已创建 {len(tables)} 个表:")
        for t in tables:
            print(f"  - {t[0]}")
        
        print("\n✅ 数据库初始化完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
