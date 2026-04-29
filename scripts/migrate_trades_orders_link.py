#!/usr/bin/env python3
"""
数据库迁移脚本：添加 trades 和 orders 关联字段

新增字段：
- live_orders.trade_id: 关联到 live_trades.id
- live_orders.trigger_order_id: 触发平仓的市场单 ID
- live_trades.tp_algo_id: 止盈条件单 ID
- live_trades.sl_algo_id: 止损条件单 ID
- live_trades.trigger_algo_id: 触发的条件单 ID

使用方式:
    python scripts/migrate_trades_orders_link.py
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

    # 1. 为 live_orders 添加 trade_id 字段
    try:
        cursor.execute("ALTER TABLE live_orders ADD COLUMN trade_id INTEGER DEFAULT 0")
        print("✅ live_orders.trade_id 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_orders.trade_id 字段已存在，跳过")
        else:
            raise

    # 2. 为 live_trades 添加 tp_algo_id 字段
    try:
        cursor.execute("ALTER TABLE live_trades ADD COLUMN tp_algo_id INTEGER DEFAULT 0")
        print("✅ live_trades.tp_algo_id 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_trades.tp_algo_id 字段已存在，跳过")
        else:
            raise

    # 3. 为 live_trades 添加 sl_algo_id 字段
    try:
        cursor.execute("ALTER TABLE live_trades ADD COLUMN sl_algo_id INTEGER DEFAULT 0")
        print("✅ live_trades.sl_algo_id 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_trades.sl_algo_id 字段已存在，跳过")
        else:
            raise

    # 4. 为 live_trades 添加 trigger_algo_id 字段
    try:
        cursor.execute("ALTER TABLE live_trades ADD COLUMN trigger_algo_id INTEGER DEFAULT 0")
        print("✅ live_trades.trigger_algo_id 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_trades.trigger_algo_id 字段已存在，跳过")
        else:
            raise

    conn.commit()

    # 5. 为 live_orders 添加 trigger_order_id 字段
    try:
        cursor.execute("ALTER TABLE live_orders ADD COLUMN trigger_order_id INTEGER DEFAULT 0")
        print("✅ live_orders.trigger_order_id 字段已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ live_orders.trigger_order_id 字段已存在，跳过")
        else:
            raise

    conn.commit()

    # 6. 修复历史数据：更新 id=100 的订单状态
    print("\n修复历史数据...")
    print("\n修复历史数据...")

    # 检查 id=100 的订单状态
    cursor.execute("SELECT id, state, close_price, profit FROM live_orders WHERE id=100")
    row = cursor.fetchone()
    if row:
        print(f"  订单 id=100: state={row[1]}, close_price={row[2]}, profit={row[3]}")

        # 如果 state=filled 但有对应的 trade 记录，说明止盈已触发
        cursor.execute("SELECT id, trade_type, profit, order_seq_id FROM live_trades WHERE order_seq_id=100")
        trade_row = cursor.fetchone()
        if trade_row:
            print(f"  找到交易记录: id={trade_row[0]}, trade_type={trade_row[1]}, profit={trade_row[2]}")

            if row[1] == 'filled':
                # 更新订单状态为 closed
                cursor.execute("""
                    UPDATE live_orders
                    SET state = 'closed',
                        close_reason = 'take_profit',
                        close_price = take_profit_price,
                        profit = ?,
                        trade_id = ?
                    WHERE id = 100
                """, (trade_row[2], trade_row[0]))
                print("  ✅ 订单 id=100 已更新为 closed 状态")

                # 更新 trade 记录的 trigger_algo_id（从 orders 表获取 tp_order_id）
                cursor.execute("SELECT tp_order_id FROM live_orders WHERE id=100")
                tp_order_id = cursor.fetchone()[0]
                cursor.execute("""
                    UPDATE live_trades
                    SET trigger_algo_id = ?, tp_algo_id = ?
                    WHERE id = ?
                """, (tp_order_id, tp_order_id, trade_row[0]))
                print(f"  ✅ 交易记录 id={trade_row[0]} 已更新 trigger_algo_id={tp_order_id}")

    conn.commit()

    # 7. 验证迁移结果
    print("\n验证迁移结果...")

    # 查看 orders 表结构
    cursor.execute("PRAGMA table_info(live_orders)")
    columns = cursor.fetchall()
    trade_id_exists = any(col[1] == 'trade_id' for col in columns)
    trigger_order_id_exists = any(col[1] == 'trigger_order_id' for col in columns)
    print(f"  live_orders.trade_id: {'存在' if trade_id_exists else '不存在'}")
    print(f"  live_orders.trigger_order_id: {'存在' if trigger_order_id_exists else '不存在'}")

    # 查看 trades 表结构
    cursor.execute("PRAGMA table_info(live_trades)")
    columns = cursor.fetchall()
    new_fields = ['tp_algo_id', 'sl_algo_id', 'trigger_algo_id']
    for field in new_fields:
        exists = any(col[1] == field for col in columns)
        print(f"  live_trades.{field}: {'存在' if exists else '不存在'}")

    # 查看修复后的数据
    print("\n修复后的数据:")
    cursor.execute("""
        SELECT o.id, o.order_id, o.state, o.close_reason, o.profit as order_profit,
               t.id as trade_id, t.trade_type, t.profit as trade_profit, t.trigger_algo_id
        FROM live_orders o
        LEFT JOIN live_trades t ON o.id = t.order_seq_id
        WHERE o.id = 100
    """)
    row = cursor.fetchone()
    if row:
        print(f"  orders: id={row[0]}, order_id={row[1]}, state={row[2]}, close_reason={row[3]}, profit={row[4]}")
        print(f"  trades: id={row[5]}, trade_type={row[6]}, profit={row[7]}, trigger_algo_id={row[8]}")

    conn.close()
    print("\n✅ 数据库迁移完成")


if __name__ == "__main__":
    migrate()