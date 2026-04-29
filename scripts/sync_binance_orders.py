#!/usr/bin/env python3
"""
Binance 订单同步脚本

检测程序关闭期间发生的订单变化，同步到数据库。

功能：
1. 查询 Binance 最近成交订单
2. 与数据库对比，发现缺失订单
3. 自动补充缺失的订单记录
4. 计算盈亏并保存交易记录

使用方式:
    python scripts/sync_binance_orders.py [--auto-fix]
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv('.env')

import os
from binance_live import BinanceClient
from database.live_trading_db import LiveTradingDB


async def sync_orders(session_id: int = 1):
    """同步 Binance 订单到数据库"""

    # 初始化
    api_key = os.getenv('BINANCE_TESTNET_API_KEY')
    api_secret = os.getenv('BINANCE_TESTNET_SECRET_KEY')
    client = BinanceClient(api_key, api_secret, testnet=True)
    db = LiveTradingDB()
    symbol = 'BTCUSDT'

    print("=" * 60)
    print("Binance 订单同步")
    print("=" * 60)

    # 1. 获取数据库中的订单
    db_orders = db.get_orders(session_id)
    print(f"\n[数据库订单] 共 {len(db_orders)} 个:")
    db_order_ids = set()
    for o in db_orders:
        if o['order_id']:
            db_order_ids.add(o['order_id'])
        print(f"  id={o['id']}, order_id={o['order_id']}, level={o['level']}, "
              f"state={o['state']}, group_id={o['group_id']}")

    # 2. 获取 Binance 最近成交订单
    all_orders = await client._request('GET', '/fapi/v1/allOrders',
                                        {'symbol': symbol, 'limit': 50}, signed=True)

    filled_orders = [o for o in all_orders if o.get('status') == 'FILLED']
    print(f"\n[Binance 成交订单] 共 {len(filled_orders)} 个:")

    for o in filled_orders[-10:]:  # 最近10个
        order_id = o.get('orderId')
        side = o.get('side')
        order_type = o.get('type')
        avg_price = Decimal(str(o.get('avgPrice', 0)))
        qty = Decimal(str(o.get('executedQty', 0)))
        exec_time = datetime.fromtimestamp(o.get('time', 0) / 1000)

        # 标记是否在数据库中
        in_db = "✅已同步" if order_id in db_order_ids else "❌缺失"

        print(f"  orderId={order_id}, {side} {order_type}, "
              f"price={avg_price:.2f}, qty={qty:.6f}, time={exec_time}, {in_db}")

    # 3. 获取当前仓位
    positions = await client.get_positions(symbol)
    position_amt = Decimal('0')
    for p in positions:
        if p.get('symbol') == symbol:
            position_amt = Decimal(str(p.get('positionAmt', '0')))
    print(f"\n[当前仓位] {position_amt:.6f} {symbol}")

    # 4. 分析缺失的订单
    print("\n" + "=" * 60)
    print("分析缺失订单")
    print("=" * 60)

    # 查找数据库中缺失的 LIMIT BUY 订单（入场单）
    missing_entries = []
    for o in filled_orders:
        if o.get('side') == 'BUY' and o.get('type') == 'LIMIT':
            order_id = o.get('orderId')
            if order_id not in db_order_ids:
                missing_entries.append(o)

    if missing_entries:
        print(f"\n发现 {len(missing_entries)} 个缺失的入场订单:")
        for o in missing_entries:
            print(f"  orderId={o.get('orderId')}, price={o.get('avgPrice')}, "
                  f"qty={o.get('executedQty')}")

    # 查找数据库中缺失的 MARKET SELL 订单（止盈/止损平仓）
    missing_closes = []
    for o in filled_orders:
        if o.get('side') == 'SELL' and o.get('type') == 'MARKET':
            order_id = o.get('orderId')
            if order_id not in db_order_ids:
                missing_closes.append(o)

    if missing_closes:
        print(f"\n发现 {len(missing_closes)} 个缺失的平仓订单:")
        for o in missing_closes:
            print(f"  orderId={o.get('orderId')}, price={o.get('avgPrice')}, "
                  f"qty={o.get('executedQty')}")

    # 5. 提供修复建议
    print("\n" + "=" * 60)
    print("修复建议")
    print("=" * 60)

    if not missing_entries and not missing_closes:
        print("✅ 所有订单已同步，无需修复")
        return

    # 分析入场和平仓的匹配关系
    # 遍历缺失的入场单，找到对应的平仓单
    for entry in missing_entries:
        entry_qty = Decimal(str(entry.get('executedQty', 0)))
        entry_price = Decimal(str(entry.get('avgPrice', 0)))
        entry_id = entry.get('orderId')

        # 查找数量匹配的平仓单
        for close in missing_closes:
            close_qty = Decimal(str(close.get('executedQty', 0)))
            close_price = Decimal(str(close.get('avgPrice', 0)))
            close_id = close.get('orderId')

            if abs(close_qty - entry_qty) < Decimal('0.001'):
                profit = (close_price - entry_price) * entry_qty
                print(f"\n入场 {entry_id} -> 平仓 {close_id}:")
                print(f"  入场价: {entry_price:.2f}")
                print(f"  平仓价: {close_price:.2f}")
                print(f"  数量: {entry_qty:.6f}")
                print(f"  盈亏: {profit:.2f} USDT")

                # 询问是否修复
                print("\n建议 SQL:")
                print(f"""
-- 补充入场订单 (A1)
INSERT INTO live_orders (session_id, order_id, level, group_id, state, entry_price, quantity, stake_amount, take_profit_price, stop_loss_price, filled_at, created_at, first_created_at)
VALUES ({session_id}, {entry_id}, 1, 2, 'filled', {entry_price}, {entry_qty}, {entry_price * entry_qty}, 0, 0, '{datetime.fromtimestamp(entry.get('time',0)/1000)}', '{datetime.fromtimestamp(entry.get('time',0)/1000)}', '{datetime.fromtimestamp(entry.get('time',0)/1000)}');

-- 更新入场订单为已平仓（止盈）
UPDATE live_orders SET state='closed', close_reason='take_profit', close_price={close_price}, profit={profit}, closed_at='{datetime.fromtimestamp(close.get('time',0)/1000)}' WHERE order_id={entry_id};

-- 补充交易记录
INSERT INTO live_trades (session_id, order_seq_id, order_id, trade_type, level, entry_price, exit_price, quantity, profit, leverage, entry_time, exit_time)
SELECT {session_id}, id, {entry_id}, 'take_profit', 1, {entry_price}, {close_price}, {entry_qty}, {profit}, 10, filled_at, closed_at FROM live_orders WHERE order_id={entry_id};
""")


async def main():
    await sync_orders(1)


if __name__ == "__main__":
    asyncio.run(main())