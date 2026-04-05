# Autofish V2 - 链式挂单策略

基于价格波动幅度概率分布的链式挂单交易策略，集成行情状态检测、可视化分析和行情感知回测功能。

**GitHub 仓库**: https://github.com/liupeng-hub/T_autofish_bot_v2

## 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 核心算法 | `autofish_core.py` | 订单、权重计算、振幅分析 |
| 行情检测 | `market_status_detector.py` | 市场状态识别（震荡/趋势） |
| 行情可视化 | `market_status_visualizer.py` | K线图可视化、Web界面 |
| Binance回测 | `binance_backtest.py` | Binance历史数据回测 |
| Binance回测Web | `binance_backtest_web.py` | Binance回测Web管理界面 |
| Binance实盘 | `binance_live.py` | Binance实盘交易 |
| Binance实盘Web | `binance_live_web.py` | Binance实盘Web管理界面 |
| LongPort回测 | `longport_backtest.py` | 港股/美股/A股回测 |
| LongPort实盘 | `longport_live.py` | 港股/美股/A股实盘 |
| K线获取 | `binance_kline_fetcher.py` | Binance K线数据获取与缓存 |

## 目录结构

```
T_autofish_bot_v2/
├── autofish_core.py                # 核心算法模块
├── market_status_detector.py       # 行情状态检测器
├── market_status_visualizer.py     # 行情可视化系统
├── binance_backtest.py             # Binance 回测模块
├── binance_backtest_web.py         # Binance 回测 Web 管理界面
├── binance_live.py                 # Binance 实盘模块
├── binance_live_web.py             # Binance 实盘 Web 管理界面
├── binance_kline_fetcher.py        # Binance K线数据获取
├── longport_backtest.py            # LongPort 回测模块
├── longport_live.py                # LongPort 实盘模块
├── web_manager.sh                  # Web 服务管理脚本
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量配置
├── venv/                           # Python 虚拟环境
├── logs/                           # 日志目录
├── database/                       # 数据库文件
│   ├── live_trading.db             # 实盘交易数据库
│   ├── test_results.db             # 回测结果数据库
│   └── klines.db                   # K线缓存数据库
├── web/                            # Web 界面
│   ├── live/                       # 实盘交易界面
│   ├── test_results/               # 回测结果界面
│   └── visualizer/                 # 行情可视化界面
├── out/                            # 输出目录
├── docs/                           # 文档目录
└── README.md                       # 说明文档
```

## 快速开始

### 0. 环境准备

```bash
# 进入项目目录
cd /Users/liupeng/Documents/trae_projects/T_autofish_bot_v2

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 如果没有 .env 文件
# 编辑 .env 填入 API Key 等配置
```

### 1. Web 服务管理

使用 `web_manager.sh` 管理所有 Web 服务：

```bash
# 启动所有 Web 服务
./web_manager.sh start-all

# 启动单个服务
./web_manager.sh start live       # 实盘交易 (端口 5003)
./web_manager.sh start backtest   # 回测系统 (端口 5002)
./web_manager.sh start visualizer # 行情可视化 (端口 5001)

# 查看服务状态
./web_manager.sh status-all

# 停止服务
./web_manager.sh stop-all
./web_manager.sh stop live

# 重启服务
./web_manager.sh restart live

# 查看日志
./web_manager.sh logs live

# 启动数据库查看服务
./web_manager.sh start-db         # 启动所有数据库服务
./web_manager.sh status-db        # 查看数据库服务状态
```

**Web 服务端口**：

| 服务 | 端口 | 说明 |
|------|------|------|
| visualizer | 5001 | 行情可视化 |
| backtest | 5002 | 回测系统 |
| live | 5003 | 实盘交易管理 |
| db-live | 5010 | 实盘数据库查看 |
| db-backtest | 5011 | 回测数据库查看 |
| db-klines | 5012 | K线数据库查看 |

### 2. 实盘交易 Web 界面

启动服务后访问 http://localhost:5003

**功能**：
- 创建/管理实盘配置（Case）
- 启动/停止/暂停交易
- 查看会话状态和订单
- 查看资金历史和交易记录
- 恢复中断/异常停止的会话

**会话恢复**：
- `running` 状态：后端服务中断，可直接恢复
- `stopped` 状态：异常退出（网络错误等），可恢复并同步交易所状态

### 3. 回测系统 Web 界面

启动服务后访问 http://localhost:5002

**功能**：
- 创建/管理测试用例
- 执行回测
- 查看回测结果和交易详情
- 对比不同参数的回测效果

### 4. K 线数据获取

```bash
# 激活虚拟环境
source venv/bin/activate

# 获取 BTCUSDT 1分钟 K 线（指定日期范围）
python binance_kline_fetcher.py --symbol BTCUSDT --interval 1m --date-range "20220101-20260405"

# 获取最近 365 天的 K 线
python binance_kline_fetcher.py --symbol BTCUSDT --interval 1m --days 365

# 查看缓存状态
python binance_kline_fetcher.py --symbol BTCUSDT --interval 1m --status

# 清空缓存
python binance_kline_fetcher.py --symbol BTCUSDT --interval 1m --clear
```

**说明**：
- K 线数据缓存在 `database/klines.db`
- 支持增量更新，自动检测缺失时间段
- 需要配置代理才能访问 Binance API

### 5. 振幅分析

```bash
# 分析 BTCUSDT 日线振幅
python autofish_core.py --symbol BTCUSDT

# 分析 ETHUSDT（使用布林带入场策略）
python autofish_core.py --symbol ETHUSDT --entry-strategy bollinger

# 分析港股/美股
python autofish_core.py --symbol 700.HK --source longport
python autofish_core.py --symbol AAPL.US --source longport
```

**命令行参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --symbol | BTCUSDT | 交易对 |
| --interval | 1d | K线周期 |
| --limit | 1000 | K线数量 |
| --leverage | 10 | 杠杆倍数 |
| --source | binance | 数据源: binance 或 longport |
| --entry-strategy | atr | 入场价格策略: fixed, atr, bollinger, support, composite |

### 6. 行情状态检测

```bash
# 分析最近30天行情
python market_status_detector.py --symbol BTCUSDT --days 30 --algorithm dual_thrust

# 分析指定日期范围
python market_status_detector.py --symbol BTCUSDT --date-range 20200101-20260310 --algorithm improved
```

**算法选项**：

| 算法 | 说明 |
|------|------|
| dual_thrust | Dual Thrust 算法（推荐） |
| improved | 改进算法，结合支撑阻力、箱体震荡 |
| adx | ADX 趋势强度算法 |
| composite | 综合算法 |

### 7. 命令行回测

```bash
# 回测 BTCUSDT
python binance_backtest.py --symbol BTCUSDT --interval 1h --limit 500 --decay-factor 0.5

# 回测港股
python longport_backtest.py --symbol 700.HK --interval 1d --count 200 --decay-factor 0.5
```

### 8. 命令行实盘（可选）

虽然推荐使用 Web 界面，也可以直接命令行启动：

```bash
# 测试网
python binance_live.py --symbol BTCUSDT --testnet --decay-factor 0.5

# 主网
python binance_live.py --symbol BTCUSDT --no-testnet --decay-factor 1.0
```

## 环境配置

在项目目录下创建 `.env` 文件：

```bash
# ==================== Binance API 配置 ====================
# 测试网 API (用于测试交易)
BINANCE_TESTNET_API_KEY=your_testnet_api_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret_key

# 主网 API (实盘交易)
BINANCE_API_KEY=your_mainnet_api_key
BINANCE_SECRET_KEY=your_mainnet_secret_key

# ==================== 代理配置 ====================
# 用于访问 Binance API (国内网络需要代理)
HTTP_PROXY=http://127.0.0.1:1087
HTTPS_PROXY=http://127.0.0.1:1087

# ==================== Longport 配置 (港股/美股) ====================
LONGPORT_APP_KEY=your_app_key
LONGPORT_APP_SECRET=your_app_secret
LONGPORT_ACCESS_TOKEN=your_access_token

# ==================== 通知配置 (可选) ====================
# Server酱微信推送 (用于 Longport)
SERVERCHAN_KEY=your_serverchan_key

# 企业微信机器人
WECHAT_BOT_KEY=your_bot_key          # Longport 通知
WECHAT_WEBHOOK=your_webhook_url      # Binance 通知
```

## 数据库说明

### live_trading.db - 实盘交易数据库

| 表名 | 说明 |
|------|------|
| live_cases | 实盘配置 |
| live_sessions | 交易会话 |
| live_orders | 订单记录 |
| live_trades | 成交记录 |
| live_capital_history | 资金历史 |
| live_capital_statistics | 资金统计 |

### test_results.db - 回测结果数据库

| 表名 | 说明 |
|------|------|
| test_cases | 测试用例 |
| test_results | 回测结果 |
| trade_details | 交易详情 |
| capital_statistics | 资金统计 |
| market_visualizer_* | 行情可视化相关表 |

### klines.db - K线缓存数据库

- 表名格式：`klines_{symbol}_{interval}`
- 字段：timestamp, open, high, low, close, volume

## 核心算法

### 权重计算公式

```
权重 = 振幅 × 概率^(1/d)
```

| 衰减因子d | 策略风格 |
|-----------|----------|
| 0.5 | 激进（权重集中在前几层） |
| 1.0 | 保守（权重分布更均匀） |

### 链式挂单逻辑

1. 创建 A1 入场单
2. A1 成交后，下止盈止损条件单，同时创建 A2 入场单
3. 重复直到达到最大层级
4. 止盈/止损触发后，取消另一个条件单，重新创建该层级入场单

### 会话恢复机制

| 状态 | 含义 | 恢复方式 |
|------|------|----------|
| `running` | 服务中断 | 直接恢复，状态同步即可 |
| `stopped` | 异常停止 | 恢复后会同步交易所状态 |

退出原因保存在 `run_message` 字段，Web 界面可查看。

## 相关文档

| 文档 | 说明 |
|------|------|
| [市场模块架构说明](docs/market_module_architecture.md) | 核心模块关系与使用场景 |
| [行情检测器文档](docs/market_status_detector.md) | 行情状态检测算法详解 |
| [行情可视化设计](docs/market_visualizer_design.md) | 可视化系统设计文档 |
| [行情感知回测](docs/market_aware_backtest.md) | 行情感知回测引擎文档 |
| [入场价格策略](docs/entry_price_strategy.md) | 入场价格策略详解 |
| [实盘交易指南](docs/binance_live_guide.md) | Binance 实盘交易指南 |
| [交易算法分析](docs/trading_algorithm.md) | 交易算法详细分析 |

## 风险提示

- 本策略仅供学习和研究使用
- 加密货币交易存在高风险，请谨慎投资
- 使用实盘模块前，请确保已在测试网充分测试
- 建议先使用小额资金进行实盘验证