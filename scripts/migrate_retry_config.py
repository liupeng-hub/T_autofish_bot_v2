#!/usr/bin/env python3
"""
数据库迁移脚本：添加 retry 配置字段

为 live_cases 表添加 retry 字段，支持网络异常指数递增重试配置。

使用方式:
    python scripts/migrate_retry_config.py
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "database" / "live_trading.db"


def migrate():
    """执行数据库迁移"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("开始数据库迁移...")
    print(f"数据库路径: {DB_FILE}")

    # 1. 为 live_cases 添加 retry 字段
    try:
        cursor.execute("ALTER TABLE live_cases ADD COLUMN retry TEXT DEFAULT '{}'")
        print("✅ live_cases.retry 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_cases.retry 字段已存在，跳过")
        else:
            raise

    conn.commit()

    # 2. 验证迁移结果
    print("\n验证迁移结果...")

    cursor.execute("PRAGMA table_info(live_cases)")
    columns = cursor.fetchall()
    retry_exists = any(col[1] == 'retry' for col in columns)
    print(f"  live_cases.retry: {'存在' if retry_exists else '不存在'}")

    conn.close()
    print("\n✅ 数据库迁移完成")


if __name__ == "__main__":
    migrate()