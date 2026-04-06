# 行情状态盘中判断方案设计决策

## 文档信息

| 项目 | 内容 |
|------|------|
| 创建日期 | 2026-04-06 |
| 版本 | 1.0 |
| 相关文件 | `binance_live.py`, `market_status_detector.py` |

---

## 一、背景问题

### 1.1 发现的问题

在使用 Dual Thrust 算法进行行情状态判断时，发现以下问题：

1. **盘中状态频繁切换**：价格在轨道边界波动时，一分钟内触发 45 次状态变化
2. **参数被绕过**：日线确认参数（`down_confirm_days`、`cooldown_days`）在盘中判断时无效
3. **WebSocket 推送频率高**：订阅 `@kline_1d` 会实时推送盘中更新，频率等于价格变动频率

### 1.2 问题根源分析

```
WebSocket (@kline_1d) 事件流：
├── is_closed=false（盘中更新）→ _on_kline_update()
│   └── 简单比较：price vs upper/lower
│       └── 绕过 DualThrustAlgorithm.calculate() 的完整逻辑
│
└── is_closed=true（收盘事件）→ _on_kline_closed()
    └── 调用 algorithm.calculate()
        └── 使用完整日线确认参数
```

**核心问题**：盘中判断走的是简化逻辑，完全绕过了算法的日线确认机制。

---

## 二、算法 K线周期分析

### 2.1 各算法 K线周期配置

| 算法 | `get_kline_interval` | WebSocket 订阅 | 历史数据（修复前） |
|------|---------------------|----------------|------------------|
| DualThrust | `'1d'` | `@kline_1d` | 硬编码 `'1d'` ✅ |
| Improved | `'1d'` | `@kline_1d` | 硬编码 `'1d'` ✅ |
| ADX | `'1h'` | `@kline_1h` | 硬编码 `'1d'` ❌ |
| Composite | `'1h'` | `@kline_1h` | 硬编码 `'1d'` ❌ |
| RealTime | `'1h'` | `@kline_1h` | 硬编码 `'1d'` ❌ |

### 2.2 Dual Thrust 参数设计意图

| 参数 | 作用 | 时间级别 |
|------|------|---------|
| `n_days` | 历史天数，计算轨道宽度 | 日线 |
| `k1`, `k2` | 突破系数，控制轨道宽度 | 日线 |
| `k2_down_factor` | 下轨敏感因子（下跌更敏感） | 日线 |
| `down_confirm_days` | 下跌需连续确认天数 | **多日** |
| `cooldown_days` | 状态变化后冷却天数 | **多日** |

**结论**：这些参数都是日线/多日级别，不适用于盘中实时判断。

---

## 三、盘中判断方案对比

### 3.1 方案 A：保持订阅，忽略盘中判断

```python
async def _on_kline_update(self, kline: Dict):
    # Dual Thrust 是日线算法，盘中不判断
    return
```

| 维度 | 评估 |
|------|------|
| **优点** | 简单直接、符合算法设计、状态稳定（每天最多变化一次） |
| **缺点** | 盘中突发趋势无法提前感知 |
| **适用场景** | Dual Thrust 作为"趋势过滤器"，用于判断当天是否适合开仓 |
| **参数一致性** | ✅ 日线参数在收盘计算时有效 |

### 3.2 方案 B：保持订阅，盘中也判断

```python
async def _on_kline_update(self, kline: Dict):
    # 获取历史K线，调用算法完整逻辑
    klines = await fetcher.fetch_kline(...)
    result = self.market_detector.algorithm.calculate(klines, {})
```

| 维度 | 评估 |
|------|------|
| **优点** | 逻辑一致性（理论上） |
| **缺点** | 参数语义混乱（`down_confirm_days` 统计盘中调用次数）、状态不稳定 |
| **问题** | 算法内部状态被盘中调用污染，收盘计算时状态已混乱 |
| **参数一致性** | ❌ 日线参数被错误使用 |

### 3.3 方案 C：移除订阅，定时任务替代

```python
# 只订阅用户数据流
ws_url = f"{self.client.ws_url}/{listen_key}"

# 定时任务检查日线收盘
async def _daily_check_loop(self):
    # 每天 00:00 UTC 检查
    ...
```

| 维度 | 评估 |
|------|------|
| **优点** | 减少 WebSocket 消息量 |
| **缺点** | 收盘检测有延迟、时区问题复杂 |
| **问题** | 日线收盘时间可能不是 00:00 UTC |
| **实时性** | ❌ 收盘事件无法实时触发 |

### 3.4 方案 D：设计专门的盘中判断方法

```python
class DualThrustAlgorithm:
    def calculate_intraday(self, current_price, bands) -> MarketStatus:
        """盘中快速判断（独立参数）"""
        ...
```

| 维度 | 评估 |
|------|------|
| **优点** | 分离关注点、可配置独立参数 |
| **缺点** | 需要设计新参数、可能与日线逻辑冲突 |
| **扩展性** | ✅ 可新增盘中专用参数 |
| **工作量** | 中等 |

---

## 四、方案对比汇总

| 方案 | 稳定性 | 实时性 | 参数一致性 | 复杂度 | 推荐度 |
|------|--------|--------|-----------|--------|--------|
| A - 忽略盘中 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ | **推荐** |
| B - 盘中也判断 | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | 不推荐 |
| C - 定时任务 | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 备选 |
| D - 专门方法 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 未来扩展 |

---

## 五、最终选择

### 5.1 选择方案 A

**原因**：

1. **符合算法设计意图**：Dual Thrust 是日线级别趋势过滤器，盘中判断本就不是其设计用途
2. **参数语义正确**：日线确认参数在收盘计算时正确生效
3. **状态稳定**：每天最多变化一次，避免频繁切换
4. **实现简单**：只需在 `_on_kline_update` 中直接返回

### 5.2 实现细节

```python
async def _on_kline_update(self, kline: Dict) -> None:
    """盘中 K线更新

    Dual Thrust 是日线级别算法，盘中不进行状态判断。
    状态变化只在 K线收盘时触发（_on_kline_closed）。

    参数:
        kline: K线数据
    """
    # Dual Thrust 是日线算法，盘中更新不做状态判断
    # 未来可扩展：记录当日最高/最低价、更新 UI 显示等
    return
```

### 5.3 其他修复

同时修复了以下问题：

1. **历史数据周期动态获取**：使用 `get_kline_interval()` 替代硬编码
2. **方法命名重构**：`_on_daily_kline_closed` → `_on_kline_closed`

---

## 六、未来扩展方向

如果需要盘中风险控制（如提前止损），可考虑：

### 6.1 新增盘中专用参数

```json
{
  "dual_thrust": {
    "n_days": 4,
    "k1": 0.4,
    "k2": 0.4,
    "k2_down_factor": 0.8,
    "down_confirm_days": 2,
    "cooldown_days": 1,
    "intraday_breakout_threshold": 0.02,
    "intraday_confirm_count": 3,
    "intraday_min_interval": 10
  }
}
```

### 6.2 独立的盘中判断方法

```python
def calculate_intraday(self, current_price, bands, config) -> MarketStatus:
    """盘中判断（与日线逻辑分离）"""
    threshold = config.get('intraday_breakout_threshold', 0.02)
    
    # 突破幅度超过阈值才触发
    upper_break = (current_price - bands['upper']) / bands['upper']
    lower_break = (bands['lower'] - current_price) / bands['lower']
    
    if upper_break > threshold:
        return MarketStatus.TRENDING_UP
    elif lower_break > threshold:
        return MarketStatus.TRENDING_DOWN
    return MarketStatus.RANGING
```

### 6.3 盘中事件的其他用途

即使不做状态判断，盘中事件仍可用于：
- 记录当日最高/最低价
- 更新 UI 显示当前轨道距离
- 触发价格告警通知

---

## 七、变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-04-06 | 创建文档，记录方案选择决策 |

---

*文档版本: 1.0*
*创建日期: 2026-04-06*