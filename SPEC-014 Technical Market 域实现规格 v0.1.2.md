# SPEC-014：Technical/Market 域实现规格

**版本：** v0.1.2
**状态：** Draft
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.6；SPEC-005 v0.2
**实现参考：** SPEC-013 v0.2.0（Adapter 映射、Evidence 边界、Pipeline 模式；非规范性上游）
**上游契约：**
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-004 §4 (Analysis Card 通用 Schema，含 ConstraintExport.registration_status)
- SPEC-004 §35-§40 (Technical/Market 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-005 §5 (Metric Registry)
**目标阶段：** 域实现规格 / MVP 实现前置

---

## 1. 文档目标

本 SPEC 定义 Technical/Market 能力域**内部如何工作**——从日线 OHLCV 数据到 Analysis Card 的完整管线。

- SPEC-004 §35-§40 定义了 Technical/Market 的"做什么"（WHAT），本 SPEC 定义"怎么做"（HOW）
- 本 SPEC 的确定性部分（指标计算、背离检测、VSA 分类）应全部可单元测试

### 1.1 上游契约策略

本 SPEC 新增了 SPEC-004 §36 未列出的 Evidence 类型（`divergence_metrics`、`wyckoff_metrics`）以及 SPEC-004 §38 / SPEC-005 Registry 未收录的 export_ref。处理策略采用 **Registry 治理 + 分阶段交付**（实现冻结范围见 §16）。

#### 1.1.1 Evidence 类型

- `#1–#6`：对应 SPEC-004 §36 已注册类型
- `#7–#8`：域内计算，**不写入共享 Evidence Pool**（对齐 SPEC-013 §3 P0 边界；Orchestrator 集成后再切换消费模式）

#### 1.1.2 constraint_exports 治理规则

`registration_status` 字段定义在 **SPEC-004 §9.1**（`crosslens_spec004.models.ConstraintExport`），Playbook 消费规则见 **SPEC-005 §6.4**。SPEC-014 的分阶段导出策略：

| registration_status | 含义 | can_support_hard_constraint | allowed_constraint_types |
|---|---|---|:---:|
| `registered` | 已在 SPEC-005 Registry 登记 | 按 metric 定义 | `["hard", "soft"]` |
| `unregistered_mvp_local` | MVP 本地扩展，未注册 | **MUST be false** | `["soft"]` |
| `proposed` | 已提交 SPEC-005 变更请求，待合并 | false | `["soft"]` |

**Playbook Evaluation MUST：** 拒绝任何 `registration_status != "registered"` 的 export 被 Hard Constraint 引用。

**分阶段导出策略：**

| 阶段 | constraint_exports 范围 | Hard Constraint |
|------|--------------------------|-----------------|
| **P0**（实现冻结） | 仅 §11.1 的 7 个已注册 Layer 1 metrics | 仅 `registered` 项 |
| **P1** | 追加 §11.2 背离 metrics/facts（soft-only） | 背离一律不可 hard |
| **P2** | 追加 §11.3 Wyckoff facts（soft-only） | Wyckoff 一律不可 hard |

**未注册 Layer 1 指标**（`atr_pct_14d`、`macd_histogram`、`adx_14d`、`bb_position`、`amihud_illiquidity`）在 P0–P2 **只写入 `domain_payload`**，**不进入 `constraint_exports`**，直至 SPEC-005 正式注册。

**后续阶段：** 向 SPEC-004/005 提交变更请求，正式注册新增 Evidence 类型和 export_ref。注册完成后将 `registration_status` 升级为 `registered`，方可参与 Hard Constraint。

---

## 2. 域目标与边界

Technical/Market 能力域负责分析价格行为、成交量、趋势、动量、波动率和流动性状态，为投资决策提供技术面和市场结构视角。

**Technical/Market 负责：**
1. 趋势方向与结构（均线系统、MACD 方向、ADX 强度）
2. 动量强弱与极值（RSI、Stochastic、ROC）
3. 成交量异常（放量/缩量、量价背离）
4. 波动率状态（ATR、布林带宽度）
5. 流动性评估（成交额、换手率）
6. **背离形态检测**（Regular/Hidden × Bullish/Bearish）
7. **威科夫量价分析**（阶段判定、VSA 信号、Spring/UTAD 事件）

**Technical/Market 不负责：**
1. 判断公司长期价值 → Fundamentals 域
2. 判断财务质量 → Fundamentals 域
3. 替代基本面分析
4. 单独给出长期买卖建议 → Playbook + Decision Candidate 层
5. 解释宏观或公司事件的真实影响 → Macro/Meso、Company Event 域

**A 股适配：** MVP 阶段仅支持 A 股日线数据。分钟线、Tick 数据不在 MVP 范围内。

---

## 3. 三层分析架构

Technical/Market 域采用三层架构，从底层指标到高层分析逐步递进：

```text
Layer 3: 威科夫量价分析层（自写算法）
  ├── Trading Range 检测（区间识别）
  ├── VSA 8 种信号分类
  ├── 威科夫阶段判定（Phase A-E）
  ├── Spring/UTAD 事件检测
  └── 产出：wyckoff_phase + key_event + vsa_signal + effort_result

Layer 2: 背离检测层（自写算法）
  ├── 极值点检测（scipy.signal.find_peaks）
  ├── 单调时间配对（Monotonic Pivot Pairing）
  ├── 4 种背离类型分类
  ├── 多指标确认（RSI + MACD + OBV）
  └── 产出：divergence_type + strength + confirmation_count

Layer 1: 基础指标层（TA-Lib 直接覆盖）
  ├── 均线系统：SMA/EMA 20/50/200
  ├── 动量指标：RSI/MACD/Stochastic/ADX/ROC
  ├── 波动率：ATR/Bollinger/NATR
  ├── 成交量：OBV/AD/MFI
  └── 产出：~20 个 computed metrics
```

**设计原则：**
- Layer 1 的所有计算委托给 TA-Lib，不重复实现指标公式
- Layer 2 和 Layer 3 是 SPEC-014 的核心价值——TA-Lib 不覆盖的高层分析逻辑
- 三层之间的数据流是单向的：Layer 1 → Layer 2 → Layer 3

---

## 4. Evidence Packet 类型定义

Technical/Market 域计算 8 种 Evidence 指标组。其中 #1-#6 对应 SPEC-004 §36 已定义的 Evidence Packet 类型，#7-#8 为本 SPEC 新增的域内计算类型（参见 §1.1 上游契约策略）。

| # | evidence_type | SPEC-004 注册 | TA-Lib 覆盖 | 自写逻辑 | 说明 |
|---|---|:---:|:---:|:---:|---|
| 1 | `moving_average_metrics` | ✅ | ✅ | — | 均线系统 |
| 2 | `momentum_metrics` | ✅ | ✅ | — | 动量指标 |
| 3 | `volatility_metrics` | ✅ | ✅ | — | 波动率指标 |
| 4 | `volume_metrics` | ✅ | ✅ | — | 成交量指标 |
| 5 | `liquidity_metrics` | ✅ | 部分 | 部分 | 流动性（需换手率数据） |
| 6 | `price_trend_metrics` | ✅ | ✅ | — | 趋势综合判断 |
| 7 | `divergence_metrics` | ❌ 新增 | ❌ | ✅ | 背离形态检测 |
| 8 | `wyckoff_metrics` | ❌ 新增 | ❌ | ✅ | 威科夫量价分析 |

> **注：** `support_resistance_metrics` 和 `market_microstructure_metrics`（SPEC-004 §36 列出）不在 MVP 范围内。`market_microstructure_metrics` 中的 `bid_ask_spread_proxy` 亦不在 MVP 范围内（参见 §16.2）。

### 4.0.1 Evidence 架构边界

> 对齐 SPEC-013 §3 的 P0 声明：域是 Evidence 的**消费者**，不回流共享池。

Technical/Market 域从 Adapter 的 `get_market_data()` 获取日线 OHLCV 原始数据，在域内计算全部 metrics。域内计算的 Evidence 不写入共享 Evidence Pool——Orchestrator 集成后再切换为消费模式。

**MVP 例外：** 由于 Context & Evidence Layer（SPEC-003 Layer 3）尚未实现，域内直接从 Adapter 获取原始数据并计算，不经过 Evidence Pool。

### 4.1 各 Evidence Packet 的完整定义

#### 4.1.1 moving_average_metrics

```text
evidence_type: "moving_average_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (close)，使用复权价格（参见 §5.3）
获取频率: 日线

metrics:
  sma_20d: float              # TA-Lib SMA(close, 20)
  sma_50d: float              # TA-Lib SMA(close, 50)
  sma_200d: float             # TA-Lib SMA(close, 200)
  ema_12d: float              # TA-Lib EMA(close, 12)
  ema_26d: float              # TA-Lib EMA(close, 26)
  price_above_20d_ma: bool
  price_above_50d_ma: bool
  price_above_200d_ma: bool
  ma_20d_slope_5d: float      # (SMA20_today - SMA20_5d_ago) / SMA20_5d_ago
  ma_50d_slope_5d: float
  golden_cross_recent: bool   # SMA50 上穿 SMA200（近 20 日内）
  death_cross_recent: bool    # SMA50 下穿 SMA200（近 20 日内）
```

**数据要求：** 至少 220 个交易日（计算 SMA200 需要 200 日 + 20 日交叉观察窗口）。

#### 4.1.2 momentum_metrics

```text
evidence_type: "momentum_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (close, high, low)

metrics:
  rsi_14d: float              # TA-Lib RSI(close, 14)，0-100
  macd_line: float            # TA-Lib MACD 的 DIF
  macd_signal: float          # TA-Lib MACD 的 DEA
  macd_histogram: float       # DIF - DEA
  macd_above_zero: bool
  macd_above_signal: bool
  stoch_k: float              # TA-Lib STOCH 的 %K (14,3,0)
  stoch_d: float              # TA-Lib STOCH 的 %D
  adx_14d: float              # TA-Lib ADX(high, low, close, 14)
  roc_10d: float              # TA-Lib ROC(close, 10)，百分比
  mom_10d: float              # TA-Lib MOM(close, 10)
```

#### 4.1.3 volatility_metrics

```text
evidence_type: "volatility_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (high, low, close)

metrics:
  atr_14d: float              # TA-Lib ATR(high, low, close, 14)
  atr_pct_14d: float          # atr_14d / close * 100
  natr_14d: float             # TA-Lib NATR(high, low, close, 14)
  bb_upper: float             # TA-Lib BBANDS 上轨
  bb_middle: float            # TA-Lib BBANDS 中轨（SMA20）
  bb_lower: float             # TA-Lib BBANDS 下轨
  bb_width: float             # (upper - lower) / middle
  bb_position: float          # (close - lower) / (upper - lower)，0-1
  stddev_20d: float           # TA-Lib STDDEV(log_returns, 20)，对数收益率标准差
  hist_vol_20d: float         # 20日年化波动率 = stddev(log_returns, 20) * sqrt(252)
```

#### 4.1.4 volume_metrics

```text
evidence_type: "volume_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (volume, high, low, close)

metrics:
  volume_vs_20d_average: float    # 今日成交量 / SMA(volume, 20)。export_ref: metric://volume_vs_20d_average
  volume_vs_5d_average: float     # 今日成交量 / SMA(volume, 5)
  obv: float                  # TA-Lib OBV(close, volume)，最新值
  obv_slope_5d: float         # OBV 5日变化率
  ad_line: float              # TA-Lib AD(high, low, close, volume)
  ad_osc: float               # TA-Lib ADOSC(high, low, close, volume, 3, 10)
  mfi_14d: float              # TA-Lib MFI(high, low, close, volume, 14)
```

> **注：** `average_dollar_volume_20d` 仅在 `liquidity_metrics` 中定义（§4.1.5），不在此处重复。`volume_vs_20d_average` 命名对齐 SPEC-004 §38 的 `metric://volume_vs_20d_average`。

#### 4.1.5 liquidity_metrics

```text
evidence_type: "liquidity_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (amount, volume, close) + stock_dailybasic (turnover_rate)

metrics:
  average_dollar_volume_20d: float  # 20日平均成交额（万元）。export_ref: metric://average_dollar_volume_20d
  turnover_rate_20d: float          # 20日平均换手率（来源: stock_dailybasic.turnover_rate，如有）
  amihud_illiquidity: float         # Amihud = mean(|return| / dollar_volume, 20)
```

> **Amihud 非流动性指标：** `|daily_return| / dollar_volume` 的 20 日均值。值越大表示流动性越差。这是学术界广泛使用的流动性代理指标（Amihud 2002）。
>
> **amount 单位：** Tushare `amount` 字段单位为**千元**。计算 `average_dollar_volume_20d` 时需除以 10 转换为万元。
>
> **turnover_rate 降级：** 若 `stock_dailybasic` 无 `turnover_rate` 数据，`turnover_rate_20d` 设为 `None`，Liquidity Classifier 仅依赖 `average_dollar_volume_20d` 判定。

#### 4.1.6 price_trend_metrics

```text
evidence_type: "price_trend_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: stock_daily (close)

metrics:
  close: float                # 最新收盘价
  change_1d: float            # 1日涨跌幅
  change_5d: float            # 5日涨跌幅
  change_20d: float           # 20日涨跌幅
  drawdown_from_52w_high: float  # 距52周最高点的回撤比例。export_ref: metric://drawdown_from_52w_high
  drawdown_from_52w_low: float   # 距52周最低点的涨幅比例
  distance_from_sma200: float    # (close - sma_200d) / sma_200d
```

#### 4.1.7 divergence_metrics（Layer 2，自写算法）

```text
evidence_type: "divergence_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: false   # MVP P1+ 亦保持 false；背离仅作 Soft Constraint（§1.1.2、§11.2）
数据来源: stock_daily + Layer 1 指标

metrics:
  rsi_divergence_type: str    # "regular_bullish" | "regular_bearish" | "hidden_bullish" | "hidden_bearish" | "none"
  rsi_divergence_strength: float  # 0.0-1.0
  macd_divergence_type: str   # 同上
  macd_divergence_strength: float
  obv_divergence_type: str    # 量价背离
  divergence_confirmations: int   # RSI + MACD + OBV 中确认背离的数量（0-3）。字段名为复数形式
  divergence_lookback_days: int   # 最近一次背离距今天数
```

**背离分类定义（4 种类型）：**

| 类型 | 价格 | 指标 | 含义 | 方向 |
|------|------|------|------|------|
| **Regular Bullish**（底背离） | Lower Low (LL) | Higher Low (HL) | 下跌动能减弱 | 反转看涨 |
| **Regular Bearish**（顶背离） | Higher High (HH) | Lower High (LH) | 上涨动能减弱 | 反转向跌 |
| **Hidden Bullish**（隐藏看涨） | Higher Low (HL) | Lower Low (LL) | 趋势回调中动能充足 | 延续看涨 |
| **Hidden Bearish**（隐藏看跌） | Lower High (LH) | Higher High (HH) | 趋势反弹中动能不足 | 延续看跌 |

**背离强度评分规则：** 详见 §7.4（唯一权威定义）。本节不重复。

#### 4.1.8 wyckoff_metrics（Layer 3，自写算法）

```text
evidence_type: "wyckoff_metrics"
generation_type: computed
determinism_level: structured    # 包含启发式判断
can_support_hard_constraint: false   # 威科夫分析是结构性判断，不支撑 Hard Constraint
数据来源: stock_daily (OHLCV)

metrics:
  wyckoff_phase: str          # "accumulation" | "markup" | "distribution" | "markdown" | "unknown"
  wyckoff_sub_phase: str      # "A" | "B" | "C" | "D" | "E" | "none"
  key_event: str              # "spring" | "utad" | "sos" | "sow" | "sc" | "bc" | "ar" | "st" | "lps" | "lpsy" | "none"
  event_confidence: float     # 0.0-1.0
  trading_range_high: float   # 当前识别到的区间上沿（如有）
  trading_range_low: float    # 当前识别到的区间下沿（如有）
  trading_range_days: int     # 区间持续时间（交易日）
  vsa_signal: str             # "demand" | "supply" | "no_demand" | "no_supply" | "stopping_volume" | "absorption" | "effort_result_divergence" | "change_of_character" | "none"
  effort_result: str          # "aligned" | "divergence" | "unknown"
  is_limit_up: bool           # 当日涨停（A 股特殊标记）
  is_limit_down: bool         # 当日跌停（A 股特殊标记）
```

> **重要：** `wyckoff_metrics` 的 `determinism_level` 设为 `structured`（而非 `computed`），因为威科夫阶段判定包含启发式规则，相同输入在不同参数下可能产生不同结果。因此 `can_support_hard_constraint = false`。
>
> **涨跌停标记：** `is_limit_up` / `is_limit_down` 用于 VSA 分类时的降级处理。涨停/跌停日的 VSA 信号 `event_confidence` 降低 0.2（参见 §8.3）。

---

## 5. 确定性指标计算规范（Layer 1）

### 5.1 TA-Lib 调用约定

所有 Layer 1 指标通过 TA-Lib 计算。调用约定：

```python
import talib
import numpy as np

# 输入数据格式：numpy array，按日期升序排列，使用复权价格（参见 §5.3）
close = np.array([...], dtype=float)
high = np.array([...], dtype=float)
low = np.array([...], dtype=float)
volume = np.array([...], dtype=float)

# TA-Lib 返回的 array 中，前 N-1 个元素为 NaN（warmup period）
# 取最后一个非 NaN 值作为最新指标
rsi = talib.RSI(close, timeperiod=14)
rsi_latest = rsi[~np.isnan(rsi)][-1]
```

**数据长度要求：**

| 指标 | 最少数据量 | 推荐数据量 | 说明 |
|------|:---------:|:---------:|------|
| SMA(200) | 200 | 250 | 需要 200 日 + 交叉观察窗口 |
| RSI(14) | 15 | 30 | warmup 14 日 |
| MACD(12,26,9) | 35 | 60 | warmup 26+9 日 |
| BBANDS(20) | 20 | 30 | warmup 20 日 |
| ATR(14) | 15 | 30 | warmup 14 日 |
| ADX(14) | 28 | 50 | warmup 2×period |
| STOCH(14,3) | 17 | 30 | warmup 14+3 日 |

**推荐最小数据量：250 个交易日**（覆盖 SMA200 + 背离检测窗口）。

**TA-Lib 部署注意事项：** TA-Lib C 库在 Windows 上需要预编译二进制。若安装失败，使用 `pandas-ta` 作为 fallback（API 兼容层需单独封装）。MVP 阶段 MockAdapter 测试不依赖 TA-Lib。

### 5.2 派生指标计算

以下指标 TA-Lib 不直接提供，需要简单的派生计算：

**均线斜率（5 日）：**
```python
sma = talib.SMA(close, timeperiod=period)
slope = (sma[-1] - sma[-6]) / sma[-6]  # 5日变化率
```

**布林带位置：**
```python
upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
bb_position = (close[-1] - lower[-1]) / (upper[-1] - lower[-1])
```

**布林带宽度：**
```python
bb_width = (upper[-1] - lower[-1]) / middle[-1]
```

**距 52 周高/低点：**
```python
high_52w = np.max(high[-252:])  # 52周 ≈ 252 交易日
low_52w = np.min(low[-252:])
drawdown_from_high = (close[-1] - high_52w) / high_52w
distance_from_low = (close[-1] - low_52w) / low_52w
```

**历史波动率（20日年化）：**
```python
returns = np.diff(np.log(close))
stddev = talib.STDDEV(returns, timeperiod=20)
hist_vol = stddev[-1] * np.sqrt(252)
```

**Amihud 非流动性指标：**
```python
# dollar_volume 使用 amount 字段（单位: 千元 → 转为万元: /10）
dollar_volume = amount / 10.0  # 万元
abs_return = np.abs(np.diff(np.log(close)))
amihud_daily = abs_return / dollar_volume[:-1]
amihud_20d = np.mean(amihud_daily[-20:])
```

**金叉/死叉检测（近 20 日）：**
```python
sma50 = talib.SMA(close, 50)
sma200 = talib.SMA(close, 200)
# 金叉：SMA50 从下方穿越 SMA200
golden_cross = any(
    sma50[i-1] < sma200[i-1] and sma50[i] > sma200[i]
    for i in range(-20, 0)
)
```

### 5.3 复权价格规则

**原则：** 所有技术指标计算使用**前复权价格**，以消除除权除息对均线和极值点检测的干扰。

**复权公式：**
```python
# adj_factor 序列：当日复权因子
# 前复权价格 = 原始价格 × (adj_factor / adj_factor[-1])
# 这样最新日的价格 = 原始收盘价，历史价格按比例调整
close_adj = close * (adj_factor / adj_factor[-1])
high_adj = high * (adj_factor / adj_factor[-1])
low_adj = low * (adj_factor / adj_factor[-1])
```

**对分析的影响：**

| 指标 | 不复权的问题 | 前复权的效果 |
|------|-------------|-------------|
| SMA(200) | 除权导致均线断崖 | 平滑连续 |
| 52 周高/低点 | 除权前的高点失真 | 真实可比 |
| 背离极值点 | 除权产生虚假极值 | 消除干扰 |
| ATR | 除权日 ATR 异常放大 | 真实波动 |

**Adapter 要求：** `crosslens_adapters` 的 `get_market_data()` 必须提供真实的 `adj_factor`。当前 AlphaDB 实现中 `adj_factor = 1.0`（未复权），**需在 Phase 1.5 后续补充**：从 `rawdata.stock_adj_factor` 表获取复权因子。MVP 阶段若 `adj_factor` 全为 1.0，在 `warnings` 中记录 `"price_not_adjusted: 使用未复权价格，均线和极值点可能受除权影响"`。

---

## 6. 分类器定义

### 6.1 分类器总览

| # | 分类器 | 输入 | 输出 | 层级 |
|---|--------|------|------|------|
| 1 | Trend Classifier | moving_average_metrics, momentum_metrics | `trend_state` | Layer 1 |
| 2 | Momentum Classifier | momentum_metrics | `momentum_state` | Layer 1 |
| 3 | Volume Classifier | volume_metrics | `volume_state` | Layer 1 |
| 4 | Volatility Classifier | volatility_metrics | `volatility_state` | Layer 1 |
| 5 | Liquidity Classifier | liquidity_metrics | `liquidity_state` | Layer 1 |
| 6 | Divergence Classifier | divergence_metrics | `divergence_assessment` | Layer 2 |
| 7 | Wyckoff Phase Classifier | wyckoff_metrics | `wyckoff_assessment` | Layer 3 |

### 6.2 Trend Classifier

**输入**：`price_above_20d_ma`, `price_above_50d_ma`, `price_above_200d_ma`, `ma_50d_slope_5d`, `ma_20d_slope_5d`, `golden_cross_recent`, `death_cross_recent`

**输出**：`uptrend` | `downtrend` | `sideways` | `trend_reversal` | `unknown`

**判定规则**：

```text
IF price_above_20d_ma AND price_above_50d_ma AND price_above_200d_ma
   AND ma_50d_slope_5d > 0.005:
    → "uptrend"

ELIF NOT price_above_20d_ma AND NOT price_above_50d_ma
     AND ma_50d_slope_5d < -0.005:
    → "downtrend"

ELIF abs(ma_50d_slope_5d) < 0.005
     AND abs(ma_20d_slope_5d) < 0.01:
    → "sideways"

ELIF (golden_cross_recent OR death_cross_recent)
     AND abs(ma_20d_slope_5d) > 0.01:
    → "trend_reversal"

ELSE:
    → "unknown"
```

> **阈值说明：** 0.005 = 5 日内变化 0.5%，约等于年化 25%。此阈值未经回测校准（参见 §14 开放问题）。MVP 阶段在 `domain_payload` 中标注 `threshold_calibration: "uncalibrated"`。

### 6.3 Momentum Classifier

**输入**：`rsi_14d`, `macd_histogram`, `macd_above_zero`, `stoch_k`

**输出**：`positive` | `positive_but_extended` | `neutral` | `negative` | `negative_but_oversold` | `unknown`

**判定规则**：

```text
IF rsi_14d > 70:
    → "positive_but_extended"   # 超买，动能强但过热

ELIF rsi_14d > 55 AND macd_histogram > 0 AND stoch_k > 50:
    → "positive"

ELIF rsi_14d < 30:
    → "negative_but_oversold"   # 超卖，动能弱但可能反弹

ELIF rsi_14d < 45 AND macd_histogram < 0 AND stoch_k < 50:
    → "negative"

ELIF 45 <= rsi_14d <= 55:
    → "neutral"

ELSE:
    → "unknown"
```

### 6.4 Volume Classifier

**输入**：`volume_vs_20d_average`

**输出**：`above_average` | `normal` | `below_average` | `abnormal_spike` | `unknown`

**判定规则**：

```text
IF volume_vs_20d_average > 2.0:
    → "abnormal_spike"
ELIF volume_vs_20d_average > 1.3:
    → "above_average"
ELIF volume_vs_20d_average < 0.7:
    → "below_average"
ELIF volume_vs_20d_average is None:
    → "unknown"
ELSE:
    → "normal"
```

### 6.5 Volatility Classifier

**输入**：`atr_pct_14d`, `bb_width`, `natr_14d`

**输出**：`low` | `normal` | `high` | `extreme` | `unknown`

**判定规则**：

```text
IF atr_pct_14d is None:
    → "unknown"
ELIF atr_pct_14d < 1.5:
    → "low"
ELIF atr_pct_14d < 3.5:
    → "normal"
ELIF atr_pct_14d < 6.0:
    → "high"
ELSE:
    → "extreme"
```

> **A 股语境：** A 股涨跌停板 ±10%（科创板 ±20%），日均 ATR% 通常在 2-4%。上述阈值基于此背景。

### 6.6 Liquidity Classifier

**输入**：`average_dollar_volume_20d`, `turnover_rate_20d`, `amihud_illiquidity`

**输出**：`sufficient` | `thin` | `poor` | `unknown`

**判定规则**：

```text
IF average_dollar_volume_20d is None:
    → "unknown"
ELIF average_dollar_volume_20d > 5000 (万元) AND (turnover_rate_20d > 0.01 OR turnover_rate_20d is None):
    → "sufficient"              # 日均成交额 > 5000万
ELIF average_dollar_volume_20d > 1000:
    → "thin"                    # 日均成交额 1000-5000万
ELSE:
    → "poor"                    # 日均成交额 < 1000万
```

### 6.7 Divergence Classifier（Layer 2）

**输入**：`divergence_metrics` 中的各字段

**输出**：`divergence_assessment` 字典

```text
divergence_assessment:
  has_regular_bullish: bool
  has_regular_bearish: bool
  has_hidden_bullish: bool
  has_hidden_bearish: bool
  strongest_type: str           # 最强的背离类型
  strongest_strength: float     # 最强背离的强度
  multi_indicator_confirmed: bool  # divergence_confirmations >= 2
  summary: str                  # 人类可读的背离摘要
```

**判定规则**：

```text
# 收集所有指标的背离状态
rsi_type = divergence_metrics.rsi_divergence_type
macd_type = divergence_metrics.macd_divergence_type
obv_type = divergence_metrics.obv_divergence_type
confirmations = divergence_metrics.divergence_confirmations  # 注意：复数形式

# 判断多指标确认
multi_confirmed = confirmations >= 2

# 确定最强背离
candidates = []
for indicator, type, strength in [
    ("rsi", rsi_type, rsi_strength),
    ("macd", macd_type, macd_strength),
    ("obv", obv_type, obv_strength),
]:
    if type != "none":
        candidates.append((type, strength, indicator))

if candidates:
    strongest = max(candidates, key=lambda x: x[1])
    strongest_type = strongest[0]
    strongest_strength = strongest[1]
else:
    strongest_type = "none"
    strongest_strength = 0.0
```

### 6.8 Wyckoff Phase Classifier（Layer 3）

详见 §8.5（威科夫阶段判定算法）。

---

## 7. 背离检测算法（Layer 2）

### 7.1 算法概览

背离检测的核心挑战是**在噪音中识别有意义的极值点对**。本 SPEC 采用基于 scipy 的极值点检测 + 单调时间配对方案。

```text
输入: price_series (close), indicator_series (RSI/MACD histogram/OBV)
步骤:
  1. find_peaks: 找价格序列的局部极大/极小值
  2. find_peaks: 找指标序列的局部极大/极小值
  3. 对价格和指标分别提取 swing highs 和 swing lows
  4. 单调时间配对: 每对相邻的价格极值 → 找最近的指标极值
  5. 判断背离类型
  6. 计算背离强度
输出: list[DivergenceEvent]
```

### 7.2 极值点检测

```text
参数:
  lookback: int = 7          # 滑动窗口半宽度（用于 find_peaks 的 order 参数）
  min_distance: int = 10     # 两个极值点最小间距（交易日）
  prominence_pct: float = 0.03  # 极值点显著性（3%）

算法:
  # 价格 swing highs
  price_highs_idx = scipy.signal.find_peaks(
      price,
      prominence=price.mean() * prominence_pct,
      distance=min_distance
  )[0]
  
  # 价格 swing lows（对负序列找 peaks）
  price_lows_idx = scipy.signal.find_peaks(
      -price,
      prominence=price.mean() * prominence_pct,
      distance=min_distance
  )[0]
  
  # 指标同理
  indicator_highs_idx = scipy.signal.find_peaks(indicator, ...)
  indicator_lows_idx = scipy.signal.find_peaks(-indicator, ...)
```

### 7.3 单调时间配对

```text
参数:
  max_lag: int = 5           # 价格和指标极值点最大时间差（交易日）

算法:
  对于每对相邻的价格 swing lows (i, i+1):
    # 找 ±max_lag 范围内最近的指标 swing low
    ind_low_1 = nearest_indicator_low(price_low_idx[i], max_lag)
    ind_low_2 = nearest_indicator_low(price_low_idx[i+1], max_lag)
    
    # 单调性约束: ind_low_2 必须在 ind_low_1 之后
    if ind_low_2 is None or ind_low_2 <= ind_low_1:
        continue
    
    # 判断背离
    price_lower = price[price_low_idx[i+1]] < price[price_low_idx[i]]
    indicator_higher = indicator[ind_low_2] > indicator[ind_low_1]
    
    if price_lower and indicator_higher:
        → Regular Bullish Divergence
```

> **单调性约束是关键**：确保指标极值点的配对也是时间递增的，避免回溯导致的虚假匹配。

### 7.4 背离强度评分（唯一权威定义）

```text
divergence_strength = base_score + zone_bonus + distance_bonus + confirmation_bonus

base_score = 0.2  # 所有检测到的背离至少 0.2

zone_bonus:
  # Regular Bullish: 第一个 RSI 谷在超卖区
  IF rsi_first_trough < 30: +0.3
  ELIF rsi_first_trough < 40: +0.15
  
  # Regular Bearish: 第一个 RSI 峰在超买区
  IF rsi_first_peak > 70: +0.3
  ELIF rsi_first_peak > 60: +0.15
  
  # Hidden divergences: 无 zone bonus
  ELSE: +0.0

distance_bonus:
  # 两个极值点间距 15-40 日最理想
  gap = abs(idx2 - idx1)
  IF 15 <= gap <= 40: +0.2
  ELIF 10 <= gap <= 60: +0.1
  ELSE: +0.0

confirmation_bonus:
  # 多指标确认
  IF divergence_confirmations >= 2: +0.2
  ELSE: +0.0

总分上限: 1.0
```

> **注意：** §4.1.7 仅引用本节，不重复定义。本节的评分公式是唯一权威实现。

### 7.5 背离检测的数据要求

| 指标 | 最少数据量 | 推荐数据量 |
|------|:---------:|:---------:|
| RSI 背离 | 60 日 | 120 日 |
| MACD 背离 | 80 日 | 120 日 |
| OBV 背离 | 60 日 | 120 日 |

---

## 8. 威科夫量价分析算法（Layer 3）

### 8.1 算法概览

威科夫分析分三步：

```text
Step 1: Trading Range 检测 → 识别当前是否处于横盘区间
Step 2: VSA 信号分类 → 对每根 K 线做量价分析
Step 3: 阶段判定 → 综合区间、VSA 信号、关键事件，判定当前威科夫阶段
```

### 8.2 Trading Range 检测

```text
参数:
  min_range_days: int = 20       # 区间最少持续 20 个交易日
  range_width_pct: float = 0.15  # 区间宽度不超过 15%（(high-low)/low）
  pivot_lookback: int = 10       # 极值点检测的回看窗口

算法:
  1. 用 rolling window 检测近期的高低点
  2. 如果最近 min_range_days 日内，价格波动在 range_width_pct 范围内
  3. 且至少有 2 次触及区间上沿、2 次触及区间下沿
  4. → 确认为 Trading Range
  5. 记录: range_high, range_low, start_date

输出:
  in_trading_range: bool
  range_high: float | None
  range_low: float | None
  range_start: str | None      # YYYYMMDD
  range_days: int
```

### 8.3 VSA 信号分类（8 种类型）

VSA（Volume Spread Analysis）是威科夫方法的核心工具。每根 K 线被分类为以下 8 种信号之一：

```text
输入: 单根 K 线的 (open, high, low, close, volume) + 历史均线

# 基础分类
vol_ma = SMA(volume, 20)
spread_ma = SMA(high - low, 20)
vol_ratio = volume / vol_ma
spread_ratio = (high - low) / spread_ma
close_position = (close - low) / (high - low)  # 0=收在最低, 1=收在最高

# 量级分类
IF vol_ratio > 2.0: vol_class = "ultra"
ELIF vol_ratio > 1.5: vol_class = "high"
ELIF vol_ratio < 0.7: vol_class = "low"
ELSE: vol_class = "normal"

# 价差分类
IF spread_ratio > 1.5: spread_class = "wide"
ELIF spread_ratio < 0.7: spread_class = "narrow"
ELSE: spread_class = "normal"
```

**8 种 VSA 信号判定（按优先级从高到低）：**

| 优先级 | 信号 | 量级 | 价差 | 收盘位置 | 趋势背景 |
|:------:|------|:----:|:----:|:--------:|:--------:|
| 1 | **Change of Character** | ultra | wide | 反向极端 | 趋势反转 |
| 2 | **Effort vs Result Divergence** | high+ | narrow | 任意 | 趋势方向 |
| 3 | **Absorption** | high+ | narrow | 中部(0.3-0.7) | 任意 |
| 4 | **Stopping Volume** | ultra | wide | 中部 | 下跌中 |
| 5 | **Demand Bar** | high+ | wide | 近高点(>0.7) | 下跌/横盘 |
| 6 | **Supply Bar** | high+ | wide | 近低点(<0.3) | 上涨/横盘 |
| 7 | **No Supply** | low | narrow | 近高点(>0.7) | 下跌中 |
| 8 | **No Demand** | low | narrow | 近低点(<0.3) | 上涨中 |

```text
# 伪代码
def classify_vsa(ohlcv, vol_class, spread_class, close_position, trend_direction):
    # Priority 1: Change of Character
    if vol_class == "ultra" and spread_class == "wide":
        if trend_direction == "down" and close_position > 0.7:
            return "change_of_character"
        if trend_direction == "up" and close_position < 0.3:
            return "change_of_character"
    
    # Priority 2: Effort vs Result Divergence
    if vol_class in ("high", "ultra") and spread_class == "narrow":
        return "effort_result_divergence"
    
    # Priority 3: Absorption
    if vol_class in ("high", "ultra") and 0.3 < close_position < 0.7:
        if spread_class in ("normal", "narrow"):
            return "absorption"
    
    # Priority 4: Stopping Volume
    if vol_class == "ultra" and trend_direction == "down":
        if close_position > 0.5:
            return "stopping_volume"
    
    # Priority 5: Demand Bar
    if vol_class in ("high", "ultra") and close_position > 0.7:
        if trend_direction in ("down", "sideways"):
            return "demand"
    
    # Priority 6: Supply Bar
    if vol_class in ("high", "ultra") and close_position < 0.3:
        if trend_direction in ("up", "sideways"):
            return "supply"
    
    # Priority 7: No Supply
    if vol_class == "low" and close_position > 0.7:
        if trend_direction == "down":
            return "no_supply"
    
    # Priority 8: No Demand
    if vol_class == "low" and close_position < 0.3:
        if trend_direction == "up":
            return "no_demand"
    
    return "none"
```

**涨跌停降级规则：** 当日 `is_limit_up = True` 或 `is_limit_down = True` 时：
- VSA 信号仍然计算，但 `event_confidence` 降低 0.2
- 涨停日的 `Supply Bar` 和 `No Demand` 信号不可靠（涨停封板导致无法买入，成交量低不代表无需求）
- 跌停日的 `Demand Bar` 和 `No Supply` 信号不可靠（跌停封板导致无法卖出）
- 在 `warnings` 中记录 `"limit_day_vsa_degraded: 涨跌停日 VSA 信号置信度降低"`

### 8.4 Spring/UTAD 事件检测

**Spring（弹簧，吸筹 Phase C 的关键事件）：**

```text
前提: 已识别 Trading Range (range_high, range_low)
      range_low 来自 Phase A 的 SC/ST 低点

检测条件（全部满足）:
  1. low < range_low                     # 价格跌破区间下沿
  2. close > range_low                   # 收盘收回区间内
  3. volume < sc_volume * 0.7            # 成交量比 SC 低 30%+
  4. 发生在 Phase B 之后（区间持续 > 20 日）
  
输出:
  spring_detected: bool
  spring_date: str
  spring_volume_ratio: float  # spring_vol / sc_vol
```

**UTAD（派发后上冲，派发 Phase C 的关键事件）：**

```text
前提: 已识别 Trading Range

检测条件（全部满足）:
  1. high > range_high                   # 价格突破区间上沿
  2. close < range_high                  # 收盘跌回区间内
  3. 发生在 Phase B 之后
  
输出:
  utad_detected: bool
  utad_date: str
```

### 8.5 威科夫阶段判定

```text
# 综合判定当前阶段
# 注意：使用原始均线/MACD 信号判断趋势方向，而非已离散化的 trend_state
# 原因：trend_state 的离散分类（如 sideways/trend_reversal）会丢失方向信息

def determine_wyckoff_phase(
    trading_range,     # Trading Range 检测结果
    vsa_history,       # 近 20 日 VSA 信号历史
    spring_detected,   # Spring 事件
    utad_detected,     # UTAD 事件
    ma_50d_slope,      # 原始均线斜率（连续值，非离散 trend_state）
    macd_histogram,    # 原始 MACD 柱值
    volume_trend,      # 成交量趋势（递增/递减）
) -> WyckoffAssessment:

    # 不在区间内 → 判断趋势阶段
    if not trading_range.in_range:
        # 使用原始信号而非离散 trend_state
        if ma_50d_slope > 0.005 and macd_histogram > 0:
            return WyckoffPhase(phase="markup", sub_phase="E")
        elif ma_50d_slope < -0.005 and macd_histogram < 0:
            return WyckoffPhase(phase="markdown", sub_phase="E")
        else:
            return WyckoffPhase(phase="unknown")
    
    # 在区间内 → 判断吸筹还是派发
    
    # 区间内 VSA 信号统计
    demand_count = count(vsa_history in ("demand", "no_supply"))
    supply_count = count(vsa_history in ("supply", "no_demand"))
    
    if spring_detected:
        return WyckoffPhase(phase="accumulation", sub_phase="C",
                          key_event="spring", confidence=0.7)
    
    if utad_detected:
        return WyckoffPhase(phase="distribution", sub_phase="C",
                          key_event="utad", confidence=0.7)
    
    # 无关键事件 → 根据 VSA 倾向判断
    if demand_count > supply_count * 1.5 and volume_trend == "decreasing":
        return WyckoffPhase(phase="accumulation", sub_phase="B",
                          confidence=0.4)
    
    if supply_count > demand_count * 1.5:
        return WyckoffPhase(phase="distribution", sub_phase="B",
                          confidence=0.4)
    
    return WyckoffPhase(phase="unknown")
```

> **置信度说明：** 威科夫阶段判定的置信度通常较低（0.3-0.7），因为：
> 1. Phase B 和 Phase C 的区分需要关键事件（Spring/UTAD），而这些事件可能尚未发生
> 2. 吸筹和派发在 Phase B 阶段外观相似，需要后续事件确认
> 3. 算法的启发式规则未经充分回测

---

## 9. Pipeline 实现

### 9.1 9 步管线

```text
Step 1: Input Filtering — 从 Adapter 获取日线数据（含复权因子）
Step 2: Layer 1 基础指标计算 — TA-Lib 批量计算 + 派生指标
Step 3: Layer 2 背离检测 — scipy 极值点 + 单调配对
Step 4: Layer 3 威科夫分析 — 区间检测 + VSA + 阶段判定
Step 5: Structured Classification — 7 个分类器
Step 6: Stance Determination — 技术面综合立场
Step 7: Confidence Computation — 数据质量 + 分析深度
Step 8: Analysis Card Assembly — evidence/tailwinds/headwinds/summary
Step 9: Domain Validation + Summary Template
```

### 9.2 Step 1: 数据获取

```text
# 通过 crosslens_adapters 获取日线数据
adapter = adapter_registry.get_primary()
market_data = adapter.get_market_data(ts_code, start_date, end_date)

# 数据要求: 250 个交易日的 OHLCV + adj_factor
# daily DataFrame 列: trade_date, open, high, low, close, volume, amount, adj_factor
# 按 trade_date 升序排列
```

**数据不足时的降级：**

| 数据量 | domain_status | data_quality | 说明 |
|:------:|:---:|:---:|---|
| ≥ 250 日 | completed | high | 全部三层分析可用 |
| 200-249 日 | partial | medium | SMA200 可能不可用，降级为 EMA200；`domain_status_reason = "insufficient_for_sma200"` |
| 120-199 日 | partial | medium | Layer 1 部分可用，Layer 2/3 降级 |
| 60-119 日 | partial | low | 仅 Layer 1 基础指标，Layer 2/3 不可用 |
| < 60 日 | unavailable | low | 数据不足以支撑任何分析 |

> **对齐 SPEC-004 §5.3：** `domain_status = completed` 时，所有声明为可用的分析必须实际完成。200-249 日因 SMA200 可能缺失，设为 `partial` 而非 `completed`。

### 9.3 Step 6: Stance Determination

Technical/Market 域的 stance 由 5 个 Layer 1 分类器加权决定：

```text
weights = {
    "trend": 0.30,
    "momentum": 0.25,
    "volume": 0.15,
    "volatility": 0.15,
    "liquidity": 0.15,
}

# 各分类器输出映射为数值:
label_to_score = {
    # trend_state
    "uptrend": +1.0, "downtrend": -1.0, "sideways": 0.0,
    "trend_reversal": 0.0, "unknown": 0.0,
    # momentum_state
    "positive": +1.0, "positive_but_extended": +0.5,
    "neutral": 0.0, "negative": -1.0, "negative_but_oversold": -0.5,
    "unknown": 0.0,
    # volume_state
    "above_average": +0.5, "normal": 0.0, "below_average": -0.3,
    "abnormal_spike": 0.0, "unknown": 0.0,
    # volatility_state
    "low": +0.3, "normal": 0.0, "high": -0.3, "extreme": -0.5,
    "unknown": 0.0,
    # liquidity_state
    "sufficient": +0.3, "thin": -0.3, "poor": -0.7, "unknown": 0.0,
}

raw_score = sum(weights[k] * label_to_score[labels[k]] for k in weights)

# 背离和威科夫作为调整因子
if divergence_assessment.has_regular_bullish:
    raw_score += 0.15
if divergence_assessment.has_regular_bearish:
    raw_score -= 0.15

if wyckoff_phase == "accumulation" and wyckoff_sub_phase in ("C", "D"):
    raw_score += 0.20
if wyckoff_phase == "distribution" and wyckoff_sub_phase in ("C", "D"):
    raw_score -= 0.20

# 裁剪到 [-1.0, 1.0]，防止调整因子导致越界
score = max(-1.0, min(1.0, raw_score))

# 映射到 stance
IF score > 0.5:      stance = "positive"
ELIF score > 0.2:    stance = "moderately_positive"
ELIF score < -0.5:   stance = "negative"
ELIF score < -0.2:   stance = "moderately_negative"
ELIF abs(score) <= 0.2:
    # 中性区间：无明显多空 → 直接产出 neutral（SPEC-004 §8 合法值）
    # neutral 不要求 opposing_evidence（参见 §12.2）
    stance = "neutral"
ELSE:                stance = "mixed"
```

### 9.4 Step 7: Confidence Computation

```text
# 三因子模型
evidence_confidence = _compute_evidence_conf(layer1_ok, layer2_ok, layer3_ok)
data_depth = _compute_data_depth(trading_days_count)
analysis_coverage = _compute_analysis_coverage(layer1_ok, layer2_ok, layer3_ok)

confidence = (
    evidence_confidence * 0.50 +
    data_depth * 0.30 +
    analysis_coverage * 0.20
)

# data_quality 上限
if data_quality == "low":
    confidence = min(confidence, 0.50)
elif data_quality == "medium":
    confidence = min(confidence, 0.70)
```

**_compute_evidence_conf() 公式：**

```text
# 各层证据置信：Layer 1 计算成功=1.0，失败=0.3；Layer 2/3 同理
layer_confidences = []
if layer1_ok:
    layer_confidences.append(1.0)
else:
    layer_confidences.append(0.3)
if layer2_ok:
    layer_confidences.append(0.8)   # Layer 2 略低于 Layer 1（启发式成分）
else:
    layer_confidences.append(0.2)
if layer3_ok:
    layer_confidences.append(0.6)   # Layer 3 含较多启发式判断
else:
    layer_confidences.append(0.1)

evidence_confidence = mean(layer_confidences)
```

**data_depth 计算：**

| 交易日数 | data_depth |
|:--------:|:----------:|
| ≥ 250 | 1.0 |
| 200-249 | 0.8 |
| 120-199 | 0.6 |
| 60-119 | 0.4 |
| < 60 | 0.2 |

**analysis_coverage 计算：**

| Layer | 成功 | 失败 |
|:-----:|:----:|:----:|
| Layer 1 (基础指标) | +0.5 | +0.0 |
| Layer 2 (背离检测) | +0.3 | +0.0 |
| Layer 3 (威科夫分析) | +0.2 | +0.0 |

### 9.5 Step 8: Analysis Card Assembly

#### 9.5.0 域内 Evidence 对象管理

Technical 域在域内为 8 个指标组创建 EvidencePacket 对象（对齐 SPEC-013 pipeline 模式），供 Card 组装时引用。

**evidence_id 命名规则：** `ev_tm_{type}_{run_id}`，其中 `{type}` 为 evidence_type 的缩写。

```python
# 域内 Evidence 创建（Step 2-4 完成后）
_DOMAIN_EVIDENCE_TYPES = [
    ("moving_average_metrics", "ma"),
    ("momentum_metrics",       "mom"),
    ("volatility_metrics",     "vol"),
    ("volume_metrics",         "volum"),
    ("liquidity_metrics",      "liq"),
    ("price_trend_metrics",    "trend"),
    ("divergence_metrics",     "div"),
    ("wyckoff_metrics",        "wyck"),
]

evidence_list = []
for ev_type, ev_abbrev in _DOMAIN_EVIDENCE_TYPES:
    evidence_list.append(EvidencePacket(
        evidence_id=f"ev_tm_{ev_abbrev}_{job.run_id}",
        task_id=job.task_id,
        domain=JobDomain.TECHNICAL_MARKET,
        evidence_type=ev_type,
        generation_type=GenerationType.COMPUTED,
        determinism_level=EpDeterminismLevel.COMPUTED
            if ev_type != "wyckoff_metrics"
            else EpDeterminismLevel.STRUCTURED,
        can_support_hard_constraint=(
            ev_type not in ("wyckoff_metrics", "divergence_metrics")
            # Layer 1 evidence 组本身可支撑 hard；实际 export 受 §11 registration_status 约束
        ),
        confidence=1.0 if layer_ok(ev_type) else 0.3,
        data_quality=EpDataQuality.HIGH if layer_ok(ev_type) else EpDataQuality.LOW,
    ))
```

**Required Evidence 声明（对齐 SPEC-004 §45 / evidence_coverage）：**

```python
_REQUIRED_EVIDENCE = [
    "moving_average_metrics",
    "momentum_metrics",
    "volatility_metrics",
    "volume_metrics",
    "liquidity_metrics",
    "price_trend_metrics",
]
# Layer 2/3 为 optional：缺失不降级 domain_status，但记录在 evidence_coverage 中
_OPTIONAL_EVIDENCE = ["divergence_metrics", "wyckoff_metrics"]
```

#### 9.5.1 supporting_evidence / opposing_evidence 生成规则

输出格式对齐 SPEC-004 §4：`EvidenceRef` 结构化对象（非纯字符串）。

```python
def _build_supporting(
    evidence_list: list[EvidencePacket],
    labels: dict,           # 分类器输出
    divergence_assessment: dict,
    wyckoff_assessment: dict,
) -> list[EvidenceRef]:
    """Build supporting EvidenceRef from positive signals."""
    refs = []
    label_scores = _LABEL_SCORES  # §9.3 中的 label_to_score

    # Layer 1 分类器 → supporting
    for ev_type, classifier_key in [
        ("moving_average_metrics", "trend"),
        ("momentum_metrics",       "momentum"),
        ("volume_metrics",         "volume"),
        ("volatility_metrics",     "volatility"),
        ("liquidity_metrics",      "liquidity"),
    ]:
        score = label_scores.get(labels.get(classifier_key, "unknown"), 0.0)
        if score > 0:
            ev = _find_evidence(evidence_list, ev_type)
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type=ev_type,
                    description=f"Supporting: {classifier_key} = {labels[classifier_key]}",
                    determinism_level=ev.determinism_level,
                ))

    # Layer 2 背离 → supporting
    if divergence_assessment.get("has_regular_bullish"):
        ev = _find_evidence(evidence_list, "divergence_metrics")
        if ev:
            refs.append(EvidenceRef(
                evidence_id=ev.evidence_id,
                evidence_type="divergence_metrics",
                description=f"底背离确认：{divergence_assessment['summary']}",
                determinism_level=ev.determinism_level,
            ))

    # Layer 3 威科夫 → supporting
    if (wyckoff_assessment.get("phase") == "accumulation"
            and wyckoff_assessment.get("sub_phase") in ("C", "D")):
        ev = _find_evidence(evidence_list, "wyckoff_metrics")
        if ev:
            refs.append(EvidenceRef(
                evidence_id=ev.evidence_id,
                evidence_type="wyckoff_metrics",
                description=f"威科夫吸筹 Phase {wyckoff_assessment['sub_phase']}",
                determinism_level=ev.determinism_level,
            ))

    return refs


def _build_opposing(
    evidence_list: list[EvidencePacket],
    labels: dict,
    divergence_assessment: dict,
    wyckoff_assessment: dict,
    metrics: dict,
    headwinds: list[str],
) -> list[EvidenceRef]:
    """Build opposing EvidenceRef from negative signals + fallback rules."""
    refs = []
    label_scores = _LABEL_SCORES

    # Layer 1 分类器 → opposing
    for ev_type, classifier_key in [
        ("moving_average_metrics", "trend"),
        ("momentum_metrics",       "momentum"),
        ("volume_metrics",         "volume"),
        ("volatility_metrics",     "volatility"),
        ("liquidity_metrics",      "liquidity"),
    ]:
        score = label_scores.get(labels.get(classifier_key, "unknown"), 0.0)
        if score < 0:
            ev = _find_evidence(evidence_list, ev_type)
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type=ev_type,
                    description=f"Opposing: {classifier_key} = {labels[classifier_key]}",
                    determinism_level=ev.determinism_level,
                ))

    # Layer 2 背离 → opposing
    if divergence_assessment.get("has_regular_bearish"):
        ev = _find_evidence(evidence_list, "divergence_metrics")
        if ev:
            refs.append(EvidenceRef(
                evidence_id=ev.evidence_id,
                evidence_type="divergence_metrics",
                description=f"顶背离确认：{divergence_assessment['summary']}",
                determinism_level=ev.determinism_level,
            ))

    # Layer 3 威科夫 → opposing
    if (wyckoff_assessment.get("phase") == "distribution"
            and wyckoff_assessment.get("sub_phase") in ("C", "D")):
        ev = _find_evidence(evidence_list, "wyckoff_metrics")
        if ev:
            refs.append(EvidenceRef(
                evidence_id=ev.evidence_id,
                evidence_type="wyckoff_metrics",
                description=f"威科夫派发 Phase {wyckoff_assessment['sub_phase']}",
                determinism_level=ev.determinism_level,
            ))

    # ── Fallback: 确保 directional stance 有 opposing_evidence ──
    # SPEC-004 §41 #7: stance ∈ {positive, moderately_positive, mixed,
    #   negative, moderately_negative} 时必须有 opposing_evidence
    if not refs:
        # Fallback 1: momentum 过热/过冷
        if labels.get("momentum") == "positive_but_extended":
            ev = _find_evidence(evidence_list, "momentum_metrics")
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type="momentum_metrics",
                    description="Opposing: RSI 超买，短期追高风险",
                    determinism_level=ev.determinism_level,
                ))
        # Fallback 2: 波动率异常
        if not refs and labels.get("volatility") in ("high", "extreme"):
            ev = _find_evidence(evidence_list, "volatility_metrics")
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type="volatility_metrics",
                    description=f"Opposing: 波动率 {labels['volatility']}，风险上升",
                    determinism_level=ev.determinism_level,
                ))
        # Fallback 3: 流动性不足
        if not refs and labels.get("liquidity") in ("thin", "poor"):
            ev = _find_evidence(evidence_list, "liquidity_metrics")
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type="liquidity_metrics",
                    description=f"Opposing: 流动性 {labels['liquidity']}",
                    determinism_level=ev.determinism_level,
                ))
        # Fallback 4: 从 headwinds 生成通用 opposing
        if not refs and headwinds:
            ev = _find_evidence(evidence_list, "price_trend_metrics")
            if ev:
                refs.append(EvidenceRef(
                    evidence_id=ev.evidence_id,
                    evidence_type="price_trend_metrics",
                    description=f"Opposing: {headwinds[0]}",
                    determinism_level=ev.determinism_level,
                ))

    return refs
```

> **SPEC-004 §41 #7 对齐：** `neutral` 和 `unavailable` 不在 opposing_evidence 强制范围内。仅 `positive/moderately_positive/mixed/negative/moderately_negative` 需要 opposing。Step 6 直接产出 `neutral` 可避免事后降级。

#### 9.5.2 technical_tailwinds / technical_headwinds

从分类器和背离/威科夫分析生成人类可读的顺风/逆风列表：

```text
tailwinds = []
headwinds = []

# 均线结构
if price_above_50d_ma and price_above_200d_ma:
    tailwinds.append("价格位于 50 日与 200 日均线之上")
elif not price_above_50d_ma and not price_above_200d_ma:
    headwinds.append("价格位于 50 日与 200 日均线之下")

# 动量
if momentum_state == "positive":
    tailwinds.append("动量正面：RSI={rsi_14d}, MACD 柱为正")
elif momentum_state == "positive_but_extended":
    tailwinds.append("动量强但过热：RSI={rsi_14d} > 70")
    headwinds.append("RSI 超买，短期追高风险")
elif momentum_state == "negative":
    headwinds.append("动量负面：RSI={rsi_14d}, MACD 柱为负")
elif momentum_state == "negative_but_oversold":
    headwinds.append("动量弱但超卖：RSI={rsi_14d} < 30，可能反弹")

# 成交量
if volume_state == "above_average":
    tailwinds.append("成交量高于 20 日均值（量比={volume_vs_20d_average:.1f}）")
elif volume_state == "abnormal_spike":
    headwinds.append("成交量异常放大（量比={volume_vs_20d_average:.1f}），需警惕")

# ADX
if adx_14d > 25:
    if trend_state == "uptrend":
        tailwinds.append(f"ADX={adx_14d:.0f}，上升趋势确认")
    elif trend_state == "downtrend":
        headwinds.append(f"ADX={adx_14d:.0f}，下降趋势确认")

# 背离
if has_regular_bearish_divergence and multi_indicator_confirmed:
    headwinds.append(f"多重指标顶背离确认（{divergence_confirmations} 个指标）")

# 威科夫
if wyckoff_phase == "accumulation" and sub_phase in ("C", "D"):
    tailwinds.append(f"威科夫吸筹 Phase {sub_phase}：机构建仓信号")
if wyckoff_phase == "distribution" and sub_phase in ("C", "D"):
    headwinds.append(f"威科夫派发 Phase {sub_phase}：机构出货信号")

# 流动性
if liquidity_state == "poor":
    headwinds.append(f"流动性不足：日均成交额 {average_dollar_volume_20d:.0f} 万元")
```

#### 9.5.3 summary 模板

MVP 阶段使用模板生成 summary（与 Fundamentals 域一致）：

```text
"[MVP Template] Technical analysis for {ts_code}. Status: {domain_status}, 
Stance: {stance}, Confidence: {confidence:.2f}. 
Trend: {trend_state}, Momentum: {momentum_state}, Volume: {volume_state}. 
Key signals: {tailwinds[:2] + headwinds[:2] concatenated}."
```

#### 9.5.4 key_findings 模板

```text
key_findings = []
# 最多 5 条，优先级：背离 > 威科夫事件 > 趋势 > 动量 > 成交量
if has_any_divergence:
    key_findings.append(f"背离信号：{strongest_type}（强度 {strongest_strength:.2f}，{divergence_confirmations} 指标确认）")
if key_event != "none":
    key_findings.append(f"威科夫事件：{key_event}（{wyckoff_phase} Phase {wyckoff_sub_phase}）")
if trend_state in ("uptrend", "downtrend"):
    key_findings.append(f"趋势：{trend_state}（MA50 斜率 {ma_50d_slope_5d:.3f}）")
if momentum_state in ("positive_but_extended", "negative_but_oversold"):
    key_findings.append(f"动量极值：{momentum_state}（RSI={rsi_14d:.0f}）")
if volume_state == "abnormal_spike":
    key_findings.append(f"成交量异常：量比 {volume_vs_20d_average:.1f}x")
```

#### 9.5.5 data_freshness 计算

按 SPEC-004 §4.3，Technical 域导出 Hard Constraint metrics 时 `data_freshness` 为条件必填。日线行情与财报数据不同，freshness 基于最后交易日：

```python
def _compute_data_freshness(
    daily: pd.DataFrame,          # 日线数据（含 trade_date 列）
    as_of_date: date,             # 分析基准日（通常为今天）
) -> DataFreshness:
    """Compute data_freshness for daily market data."""
    if daily.empty:
        return None
    
    last_trade_date = pd.to_datetime(daily["trade_date"].iloc[-1]).date()
    days_since_last = (as_of_date - last_trade_date).days
    
    # 交易日计数（非自然日）
    trading_days_since = count_trading_days(last_trade_date, as_of_date)
    
    if trading_days_since <= 3:
        staleness_risk = "low"
    elif trading_days_since <= 10:
        staleness_risk = "medium"
    else:
        staleness_risk = "high"
    
    return DataFreshness(
        as_of=last_trade_date.isoformat(),
        oldest_evidence_as_of=last_trade_date.isoformat(),  # 日线行情无 PIT
        newest_evidence_as_of=last_trade_date.isoformat(),
        freshness_level="daily",
        staleness_risk=staleness_risk,
        valid_until=add_trading_days(last_trade_date, 3).isoformat(),  # 3 个交易日有效（与 staleness 口径一致）
    )
```

> **日线 vs 财报 freshness：** 财报数据有 PIT（披露延迟），freshness 基于披露日。日线行情实时可得，freshness = 最后交易日距 as_of 的**交易日**数。`oldest_evidence_as_of` 和 `newest_evidence_as_of` 在 Technical 域中均为最后交易日（所有指标基于同一日的 OHLCV 计算）。
>
> **口径约定：** `staleness_risk` 和 `valid_until` 均基于**交易日**语义（`count_trading_days` / `add_trading_days`），不使用自然日 `timedelta`，避免实现混用。

#### 9.5.6 evidence_coverage 计算

```python
def _compute_evidence_coverage(
    evidence_list: list[EvidencePacket],
) -> EvidenceCoverage:
    """Compute evidence_coverage per SPEC-004 §45."""
    available_types = {e.evidence_type for e in evidence_list if e.confidence > 0.5}
    missing = [t for t in _REQUIRED_EVIDENCE if t not in available_types]
    
    return EvidenceCoverage(
        total_available=len(available_types),
        missing_required_evidence=missing,
    )
```

> **缺失处理：** `_REQUIRED_EVIDENCE` 中 6 项 Layer 1 类型若缺失，加入 `missing_required_evidence` 并可能导致 `domain_status = partial`。Layer 2/3 为 `_OPTIONAL_EVIDENCE`，缺失不影响 domain_status。

#### 9.5.7 key_risks 模板

从 headwinds 和流动性/背离信号派生：

```python
def _derive_key_risks(
    labels: dict,
    divergence_assessment: dict,
    wyckoff_assessment: dict,
) -> list[str]:
    risks = []
    
    # 流动性风险
    if labels.get("liquidity") == "poor":
        risks.append("流动性不足：日均成交额低于 1000 万，大单冲击成本高")
    elif labels.get("liquidity") == "thin":
        risks.append("流动性偏薄：日均成交额 1000-5000 万")
    
    # 波动率风险
    if labels.get("volatility") == "extreme":
        risks.append("极端波动率：短期价格波动可能超出正常范围")
    elif labels.get("volatility") == "high":
        risks.append("高波动率：注意仓位管理和止损设置")
    
    # 背离风险
    if divergence_assessment.get("has_regular_bearish"):
        risks.append("顶背离信号：上涨动能减弱，注意趋势反转风险")
    
    # 威科夫风险
    if wyckoff_assessment.get("phase") == "distribution":
        risks.append(f"威科夫派发阶段：机构可能在出货")
    
    # 超买风险
    if labels.get("momentum") == "positive_but_extended":
        risks.append("动量过热：RSI 超买区，追高风险上升")
    
    return risks
```

#### 9.5.8 invalidating_conditions 模板

```python
def _derive_invalidating_conditions(
    labels: dict,
    metrics: dict,
) -> list[str]:
    conditions = []
    
    # 均线失效条件
    if labels.get("trend") == "uptrend":
        conditions.append("价格跌破 200 日均线且连续 3 日未收回")
    elif labels.get("trend") == "downtrend":
        conditions.append("价格突破 50 日均线且连续 3 日站稳")
    
    # 背离失效条件
    conditions.append("顶背离信号被新的 MACD 金叉覆盖")
    
    # 威科夫失效条件
    conditions.append("Spring 后价格再次跌破区间低点（Spring 失败）")
    
    return conditions
```

#### 9.5.9 Analysis Card 字段必填清单

| 字段 | 必填 | 来源 |
|------|:----:|------|
| `card_id` | ✅ | `card_technical_{task_id}` |
| `schema_version` | ✅ | `"SPEC-004@0.2.6"` |
| `task_id` / `run_id` / `domain` | ✅ | 从 job 继承 |
| `domain_status` | ✅ | Step 1 数据量判定 |
| `domain_status_reason` | 条件 | partial/unavailable 时必填 |
| `summary` | ✅ | §9.5.4 模板 |
| `stance` | ✅ | Step 6 计算 |
| `confidence` / `confidence_reason` | ✅ | Step 7 计算 |
| `time_horizon` | ✅ | 默认 `"short_to_medium_term"`（人类可读摘要） |
| `time_horizon_bucket` | ✅ | 默认 `"short_term"`（机器字段，对齐 SPEC-004 冲突检测） |
| `time_horizon_days_min` | ✅ | 默认 `5` |
| `time_horizon_days_max` | ✅ | 默认 `60` |
| `data_quality` | ✅ | 从 data_depth 映射 |
| `data_freshness` | 条件 | §9.5.5（constraint_exports 非空时必填） |
| `evidence_coverage` | ✅ | §9.5.6 |
| `supporting_evidence` | ✅ | §9.5.1 EvidenceRef 列表 |
| `opposing_evidence` | 条件 | directional stance 时必填（§9.5.1 fallback） |
| `key_findings` | ✅ | §9.5.4 模板 |
| `key_risks` | ✅ | §9.5.7（可为空列表） |
| `invalidating_conditions` | ✅ | §9.5.8（可为空列表） |
| `constraint_exports` | ✅ | §11 |
| `warnings` / `limitations` | ✅ | §12 验证产出 |
| `domain_payload` | ✅ | §10 |

---

## 10. domain_payload 完整定义

### 10.1 payload 结构

```json
{
  "trend_state": "uptrend",
  "momentum_state": "positive_but_extended",
  "volume_state": "above_average",
  "volatility_state": "normal",
  "liquidity_state": "sufficient",
  
  "divergence": {
    "has_regular_bullish": false,
    "has_regular_bearish": true,
    "strongest_type": "regular_bearish",
    "strongest_strength": 0.65,
    "multi_indicator_confirmed": true,
    "summary": "RSI 顶背离 + MACD 顶背离确认，价格创新高但动量减弱"
  },
  
  "wyckoff": {
    "phase": "markup",
    "sub_phase": "E",
    "key_event": "none",
    "in_trading_range": false,
    "vsa_recent": "demand",
    "effort_result": "aligned"
  },
  
  "key_levels": {
    "support": [],
    "resistance": [],
    "source": "none",
    "note": "MVP 不交付支撑/阻力自动计算。trading_range_high/low 可作为软参考（见 wyckoff 字段）"
  },
  
  "threshold_calibration": "uncalibrated",
  
  "technical_tailwinds": [
    "价格位于 50 日与 200 日均线之上",
    "成交量高于 20 日均值"
  ],
  "technical_headwinds": [
    "RSI 接近过热区间（72）",
    "RSI + MACD 顶背离确认"
  ]
}
```

> **key_levels MVP 行为：** `support` 和 `resistance` 在 MVP 阶段**必须**为空数组 `[]`。若 Layer 3 检测到 Trading Range，`trading_range_high` / `trading_range_low` 可作为软参考（在 `wyckoff` 子对象中），**禁止**写入 `key_levels`。
>
> **契约测试约束：** `key_levels.support` 和 `key_levels.resistance` **MUST** be `[]`，除非 `support_resistance_metrics` 已正式实现并注册。任何非空输出 MUST fail contract test（`tests/test_technical_card.py::test_key_levels_must_be_empty`）。

### 10.2 枚举约束（对齐 SPEC-004 §37.1）

所有枚举值必须使用 SPEC-004 §37.1 定义的值。SPEC-014 新增的字段（需后续注册到 SPEC-004）：

#### divergence_assessment.strongest_type

```text
regular_bullish
regular_bearish
hidden_bullish
hidden_bearish
none
```

#### wyckoff_phase

```text
accumulation
markup
distribution
markdown
unknown
```

#### wyckoff_sub_phase

```text
A
B
C
D
E
none
```

#### vsa_signal

```text
demand
supply
no_demand
no_supply
stopping_volume
absorption
change_of_character
effort_result_divergence
none
```

---

## 11. constraint_exports

### 11.0 Export 治理总则

所有 `constraint_exports` 项 MUST 携带 `registration_status`（SPEC-004 §9.1，默认 `registered`；治理规则 SPEC-005 §6.4）。**P0 实现冻结**仅交付 §11.1；§11.2/§11.3 分别对应 P1/P2。

**ConstraintExport 最小结构示例（已注册 metric）：**

```json
{
  "export_type": "metric",
  "export_ref": "metric://rsi_14d",
  "evidence_ref": "ev_tm_mom_{run_id}",
  "value_path": "rsi_14d",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "allowed_constraint_types": ["hard", "soft"],
  "registration_status": "registered"
}
```

**未注册 soft-only 示例（P1 背离）：**

```json
{
  "export_type": "metric",
  "export_ref": "metric://divergence_strength",
  "evidence_ref": "ev_tm_div_{run_id}",
  "value_path": "divergence_strength",
  "determinism_level": "computed",
  "can_support_hard_constraint": false,
  "allowed_constraint_types": ["soft"],
  "registration_status": "unregistered_mvp_local"
}
```

### 11.1 Layer 1 导出的 Computed Metrics（P0 — 仅已注册）

以下 **7** 个 metrics 已在 SPEC-004 §38 / SPEC-005 Registry 登记，P0 **唯一**可导出 Hard Constraint 的 metrics（`bid_ask_spread_proxy` 虽已注册但 MVP 不交付，见 §16.2）：

| export_ref | 说明 | registration_status | can_support_hard |
|---|---|:---:|:---:|
| `metric://rsi_14d` | RSI 14日 | `registered` | true |
| `metric://price_above_50d_ma` | 价格高于50日均线 | `registered` | true |
| `metric://price_above_200d_ma` | 价格高于200日均线 | `registered` | true |
| `metric://volume_vs_20d_average` | 量比 | `registered` | true |
| `metric://atr_14d` | ATR 14日 | `registered` | true |
| `metric://drawdown_from_52w_high` | 距52周高点回撤 | `registered` | true |
| `metric://average_dollar_volume_20d` | 20日均成交额 | `registered` | true |

> **注：** `metric://bid_ask_spread_proxy`（SPEC-004 §38 已注册）不在 MVP 范围内，不导出。

### 11.4 domain_payload-only 指标（未注册，不进 constraint_exports）

以下 Layer 1 指标在 Evidence / domain_payload 中计算，但 **MUST NOT** 进入 `constraint_exports`，直至 SPEC-005 注册：

| 字段（domain_payload） | 对应 export_ref（待注册） | 说明 |
|---|---|---|
| `atr_pct_14d` | `metric://atr_pct_14d` | ATR 百分比 |
| `macd_histogram` | `metric://macd_histogram` | MACD 柱值 |
| `adx_14d` | `metric://adx_14d` | ADX 14日 |
| `bb_position` | `metric://bb_position` | 布林带位置 |
| `amihud_illiquidity` | `metric://amihud_illiquidity` | Amihud 非流动性 |

### 11.2 Layer 2 导出的 Metrics / Facts（P1 — soft-only）

背离检测依赖极值点参数（§7.2、§14.3），阈值未经 A 股回测校准。MVP 阶段**一律不支持 Hard Constraint**：

| export_ref | 说明 | registration_status | can_support_hard | allowed_constraint_types |
|---|---|:---:|:---:|:---:|
| `metric://divergence_confirmations` | 确认背离的指标数量 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://divergence_strength` | 最强背离的强度 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://has_regular_bullish_divergence` | 是否存在底背离 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://has_regular_bearish_divergence` | 是否存在顶背离 | `unregistered_mvp_local` | false | `["soft"]` |

> **设计理由：** 多指标确认可提高 confidence，但不应自动获得 hard 权限。未来若回测验证有效，通过 SPEC-005 注册为 conditional hard export。

### 11.3 Layer 3 导出（P2 — soft-only）

威科夫分析的所有输出 `can_support_hard_constraint = false`，仅作为 Soft Constraint：

| export_ref | 说明 | registration_status | can_support_hard | allowed_constraint_types |
|---|---|:---:|:---:|:---:|
| `fact://wyckoff_accumulation_phase_cd` | 吸筹 Phase C/D | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://wyckoff_distribution_phase_cd` | 派发 Phase C/D | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://wyckoff_spring_detected` | Spring 事件检测到 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://wyckoff_utad_detected` | UTAD 事件检测到 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://vsa_effort_result_divergence` | VSA 努力与结果背离 | `unregistered_mvp_local` | false | `["soft"]` |

> **设计理由：** 威科夫分析包含大量启发式判断，相同输入在不同参数下可能产生不同结论。不适合作为 Hard Constraint。

---

## 12. Domain-Level Validation

### 12.1 验证检查清单（8 项）

| # | 检查项 | 级别 | 说明 |
|---|--------|:----:|------|
| 1 | 数据不足 60 日 | block | 数据量不满足最低要求 |
| 2 | 数据 60-119 日 | flag | Layer 2/3 可能不完整 |
| 3 | Layer 1 全部指标计算失败 | flag | TA-Lib 异常 |
| 4 | Layer 2 背离检测无法运行 | note | 数据不足或无足够极值点 |
| 5 | Layer 3 威科夫分析无法运行 | note | 未识别到 Trading Range |
| 6 | stance=mixed 但无 opposing_evidence | flag | §41 质量检查 #7 |
| 7 | liquidity_state=poor 但 stance=positive | flag | 流动性风险警告 |
| 8 | divergence 和 trend_state 方向矛盾 | note | 记录但不阻断 |

### 12.2 验证检查 #6 详细说明

当 `stance ∈ {positive, moderately_positive, mixed, negative, moderately_negative}` 但 `opposing_evidence` 为空时：

```text
→ 执行 §9.5.1 的 fallback 链（momentum → volatility → liquidity → headwinds）
→ 如果 fallback 链仍产出空 opposing：
    → 如果 stance 为 mixed：降级为 "neutral"（SPEC-004 §8 合法值；
      Step 6 打分路径在 |score| ≤ 0.2 时直接产出 neutral，
      此路径仅覆盖 Step 6 产出 mixed 但后续 evidence 检查发现无 opposing 的边界情况）
    → 如果 stance 为 directional（positive/moderately_positive/negative/moderately_negative）：
      降级为 neutral，domain_status_reason = "no_opposing_evidence_for_directional_stance"
      warnings.append("directional_stance_no_opposing: 无足够反方证据支撑方向性判断，降级为 neutral")
```

> **注意：** `neutral` 是 SPEC-004 §8 的合法 stance 值，不要求 `opposing_evidence`。Step 6 在 `|score| ≤ 0.2` 时直接产出 `neutral`，可预防大部分此类降级。

### 12.3 验证检查 #7 详细说明

当 `liquidity_state = poor` 且 `stance ∈ {positive, moderately_positive}` 时：

```text
→ warnings.append("liquidity_risk_positive_stance: 流动性不足但技术面立场正面")
→ confidence = min(confidence, 0.60)  # 流动性风险降信心上限
```

### 12.4 验证检查 #8 详细说明

当背离方向和趋势方向矛盾时（如 uptrend + regular_bearish_divergence）：

```text
→ warnings.append("divergence_trend_conflict: 趋势方向与背离信号矛盾，需结合其他域确认")
```

这是正常的市场状态（强趋势中常出现背离），不阻断但记录。

---

## 13. 测试策略

### 13.1 包结构

代码落点：`src/crosslens_technical_market/`

```text
src/crosslens_technical_market/
  __init__.py
  pipeline.py              # run_technical_market_domain()
  indicators/              # Layer 1: TA-Lib 封装 + 派生指标
    __init__.py
    talib_wrapper.py       # TA-Lib 调用 + pandas-ta fallback
    derived.py             # 派生指标（斜率、BB 位置等）
  divergence/              # Layer 2: 背离检测
    __init__.py
    detector.py            # find_peaks + 单调配对
    scoring.py             # 强度评分
  wyckoff/                 # Layer 3: 威科夫分析
    __init__.py
    trading_range.py       # 区间检测
    vsa.py                 # VSA 8 种信号分类
    events.py              # Spring/UTAD 检测
    phase.py               # 阶段判定
  classifiers/             # 7 个分类器
    __init__.py
    trend.py
    momentum.py
    volume.py
    volatility.py
    liquidity.py
    divergence_classifier.py
    wyckoff_classifier.py
  stance.py                # Stance 加权打分
  confidence.py            # Confidence 三因子模型
  card.py                  # Analysis Card 组装
  validation.py            # 8 项域级验证
  templates.py             # Summary + key_findings 模板
```

### 13.2 测试分层

| 层级 | 阶段 | 测试文件 | 覆盖内容 |
|------|:----:|---------|---------|
| Layer 1 指标 | P0 | `tests/test_technical_indicators.py` | TA-Lib 调用 + 派生指标 + 复权 |
| Layer 1 分类器 | P0 | `tests/test_technical_classifiers.py` | 5 个 Layer 1 分类器 |
| Pipeline P0 | P0 | `tests/test_technical_pipeline.py` | Layer 1 端到端 + Card 组装 |
| Card 契约 | P0 | `tests/test_technical_card.py` | AnalysisCard schema + key_levels 空数组约束 |
| 集成 | P0 | `tests/integration/test_technical_real.py` | 真实数据源 Layer 1 路径 |
| Layer 2 背离 | P1 | `tests/test_divergence.py` | 4 种背离类型 + 强度评分 + 单调配对 |
| Layer 3 威科夫 | P2 | `tests/test_wyckoff.py` | VSA 分类 + Spring/UTAD + 阶段判定 + 涨跌停降级 |

### 13.3 Layer 1 测试用例

```text
# 均线
test_sma_20d_normal
test_sma_200d_insufficient_data
test_golden_cross_detection
test_death_cross_detection
test_ma_slope_positive
test_ma_slope_negative

# 动量
test_rsi_overbought (>70)
test_rsi_oversold (<30)
test_rsi_neutral (45-55)
test_macd_above_signal
test_macd_below_zero
test_adx_strong_trend (>25)
test_adx_weak_trend (<20)

# 波动率
test_atr_normal
test_atr_extreme (>6%)
test_bb_position_upper (>0.8)
test_bb_position_lower (<0.2)

# 成交量
test_volume_spike (>2.0x)
test_volume_dry_up (<0.7x)
test_obv_rising
test_obv_falling

# 复权
test_adjusted_price_continuity
test_unadjusted_price_warning
```

### 13.4 Layer 2 背离检测测试用例

```text
test_regular_bullish_divergence
test_regular_bearish_divergence
test_hidden_bullish_divergence
test_hidden_bearish_divergence
test_no_divergence
test_divergence_strength_oversold_bonus
test_divergence_strength_multi_confirmation
test_monotonic_pairing_no_backtrack
test_max_lag_filtering
test_min_distance_filtering
```

### 13.5 Layer 3 威科夫测试用例

```text
# VSA 分类
test_vsa_demand_bar
test_vsa_supply_bar
test_vsa_no_demand
test_vsa_no_supply
test_vsa_stopping_volume
test_vsa_absorption
test_vsa_effort_result_divergence
test_vsa_change_of_character
test_vsa_priority_ordering
test_vsa_limit_up_degraded
test_vsa_limit_down_degraded

# Trading Range 检测
test_trading_range_detected
test_trading_range_too_short
test_trading_range_too_wide
test_no_trading_range

# Spring/UTAD 检测
test_spring_detected
test_spring_rejected_high_volume
test_utad_detected

# 阶段判定
test_accumulation_phase_b
test_accumulation_phase_c_spring
test_distribution_phase_b
test_markup_phase
test_markdown_phase
test_unknown_phase
```

### 13.6 Card 契约测试用例（P0）

```text
test_analysis_card_schema_valid          # crosslens_spec004.models.AnalysisCard model_validate
test_key_levels_must_be_empty            # key_levels.support/resistance MUST be []
test_constraint_exports_registered_only   # P0: 仅 7 个 registration_status=registered hard exports
test_data_freshness_required_when_exports # constraint_exports 非空时 data_freshness 必填
test_time_horizon_bucket_populated       # time_horizon_bucket + days_min/max 必填
test_opposing_evidence_for_directional_stance  # §41 ¶7
```

---

## 14. 开放问题

### 14.1 阈值校准

以下阈值均为经验值，未经 A 股回测验证。MVP 阶段在 `domain_payload` 中标注 `threshold_calibration: "uncalibrated"`。

| 分类器 | 阈值 | 当前值 | 校准方法 |
|--------|------|--------|---------|
| Trend | ma_slope 阈值 | 0.005 | 回测不同阈值下的趋势预测准确率 |
| Momentum | RSI 超买/超卖 | 70/30 | 经典值，可考虑 A 股调整为 75/25 |
| Volatility | ATR% 阈值 | 1.5/3.5/6.0 | 统计 A 股 ATR% 分布后设定 |
| Volume | 量比阈值 | 1.3/2.0/0.7 | 统计 A 股量比分布后设定 |
| Liquidity | 成交额阈值 | 1000/5000 万 | 参考 A 股流动性分层研究 |

**建议校准路径（Phase 2）：**
1. 用 AlphaDB 历史数据计算各指标的分布
2. 取分位数作为阈值（如 25%/50%/75% 分位）
3. 回测不同阈值组合的预测效果

### 14.2 威科夫分析的可靠性

威科夫量价分析本质上是一种**结构化的主观判断**：
- 不同分析师对同一图表可能判定不同的阶段
- Spring/UTAD 的"快速收回"没有严格的时间定义
- Phase B 和 Phase C 的区分在实际中非常模糊

**当前设计通过以下方式缓解：**
- `confidence` 字段显式标注判定的不确定性
- Phase B 的默认置信度仅 0.4（需要后续事件确认）
- 所有威科夫输出 `can_support_hard_constraint = false`

### 14.3 背离检测的参数敏感性

背离检测的结果对参数敏感：
- `lookback` 太大 → 漏掉短期背离
- `lookback` 太小 → 产生大量噪音
- `min_distance` 太短 → 比较两个相邻微观极值点（无意义）
- `prominence_pct` 太低 → 检测到太多微小波动

**建议：** MVP 使用保守参数（lookback=7, min_distance=10, prominence=3%），优先减少假信号。

### 14.4 A 股 T+1 和涨跌停板的影响

A 股的 T+1 制度和涨跌停板限制对技术分析有独特影响：
- 涨停板当天的成交量可能异常放大但价格不动 → VSA 可能误判为 absorption
- 跌停板当天无法卖出 → 流动性分类器需要考虑
- T+1 限制了日内反转 → 短期动量指标的预测力可能不同

**MVP 处理：** 在 VSA 输入中增加 `is_limit_up` / `is_limit_down` 标记（§4.1.8）。涨跌停日的 VSA 信号 `event_confidence` 降低 0.2，并在 `warnings` 中记录。

---

## 15. 依赖清单

### 15.1 Python 依赖

| 包 | 版本 | 用途 | 安装风险 |
|---|---|---|---|
| `TA-Lib` | ≥ 0.4 | Layer 1 全部技术指标计算 | Windows 需预编译 C 库 |
| `pandas-ta` | ≥ 0.3 | TA-Lib 的 fallback | 纯 Python，无安装风险 |
| `scipy` | ≥ 1.10 | Layer 2 极值点检测 (signal.find_peaks) | 标准科学计算包 |
| `numpy` | ≥ 1.24 | 数组运算 | 标准 |
| `pandas` | ≥ 2.2 | 数据处理 | 标准 |

**TA-Lib fallback 策略：** 若 `import talib` 失败，自动切换 `pandas-ta`。封装层 `talib_wrapper.py` 负责透明切换。

### 15.2 Adapter 依赖

| 方法 | 数据源 | 说明 |
|------|--------|------|
| `adapter.get_market_data()` | AlphaDB `stock_daily` | 日线 OHLCV |
| `adapter.get_market_data()` | AlphaDB `stock_dailybasic` | 估值 + 换手率 |
| `adapter.get_market_data()` | AlphaDB `stock_adj_factor` | 复权因子（待补充） |

> **注：** Technical/Market 域不需要财务报表数据，仅需要日线行情数据。这使得它可以在没有 AlphaDB 的情况下，通过 TinyData 或其他数据源运行。

### 15.3 StandardContract 映射表

对齐 SPEC-013 §11A.4 的 Adapter 映射规范：

| StandardContract 列名 | AlphaDB 原始列名 | 说明 | 单位 |
|---|---|---|---|
| `trade_date` | `trade_date` | 交易日期 | YYYYMMDD |
| `open` | `open` | 开盘价 | 元 |
| `high` | `high` | 最高价 | 元 |
| `low` | `low` | 最低价 | 元 |
| `close` | `close` | 收盘价 | 元 |
| `volume` | `vol` | 成交量 | 手 |
| `amount` | `amount` | 成交额 | **千元**（Tushare 原始单位） |
| `adj_factor` | — | 复权因子 | 无量纲（待补充来源） |
| `turnover_rate` | `turnover_rate` | 换手率 | %（stock_dailybasic） |
| `pe_ttm` | `pe_ttm` | 市盈率 TTM | 无量纲 |
| `pb` | `pb` | 市净率 | 无量纲 |
| `total_mv` | `total_mv` | 总市值 | 万元 |

**单位转换规则：**
- `amount`（千元）→ `average_dollar_volume_20d`（万元）：除以 10
- `volume`（手）→ 用于量比计算时无需转换（比值消除单位）
- `turnover_rate`（%）→ `turnover_rate_20d`（小数）：除以 100

**缺失字段降级路径：**

| 字段 | 缺失时 | 影响 |
|------|--------|------|
| `adj_factor` | 全设为 1.0 | warning: `"price_not_adjusted"` |
| `turnover_rate` | 设为 None | Liquidity Classifier 仅依赖 `average_dollar_volume_20d` |
| `amount` | 用 `close * volume` 近似 | warning: `"amount_estimated_from_close_volume"` |

---

## 16. MVP 范围

> **分阶段交付：** P0 = 实现冻结范围（必须先完成并通过契约测试）；P1/P2 = 后续增量。算法章节（§7–§8）保留完整设计，但实现可按阶段裁剪。

### 16.1 P0 — 实现冻结（必须先交付）

- ✅ Layer 1 基础指标（TA-Lib + 派生指标 + 前复权，§5）
- ✅ 5 个 Layer 1 分类器（Trend / Momentum / Volume / Volatility / Liquidity）
- ✅ `price_trend_metrics` 计算（支撑 Trend Classifier）
- ✅ Analysis Card 完整组装（§9.5：EvidenceRef、data_freshness、evidence_coverage、time_horizon_bucket）
- ✅ `constraint_exports` **仅** §11.1 的 7 个已注册 metrics（`registration_status = "registered"`）
- ✅ `domain_payload` Layer 1 字段 + `key_levels.support/resistance = []` 契约约束
- ✅ 8 项域级验证（§12）
- ✅ AlphaDB + TinyData 集成测试（Layer 1 数据路径）
- ✅ AnalysisCard schema 契约测试（`tests/test_technical_card.py`）
- ✅ 单元测试：Layer 1 指标 + 分类器 + pipeline P0 路径

### 16.2 P1 — 背离检测（P0 完成后）

- ✅ Layer 2 背离检测（RSI + MACD + OBV，4 种类型，§7）
- ✅ Divergence Classifier（§6.7）
- ✅ `domain_payload.divergence` 子对象
- ✅ §11.2 soft-only constraint_exports（`registration_status = "unregistered_mvp_local"`）
- ✅ 单元测试：`tests/test_divergence.py`

### 16.3 P2 — 威科夫 / VSA / 校准（P1 完成后）

- ✅ Layer 3 威科夫分析（Trading Range、VSA 8 信号、Spring/UTAD、Phase A–E，§8）
- ✅ Wyckoff Phase Classifier（§6.8）
- ✅ `domain_payload.wyckoff` 子对象
- ✅ §11.3 soft-only Wyckoff facts
- ✅ 涨跌停 VSA 降级（§8.3）
- ✅ 阈值回测校准（§14.1，替换 `threshold_calibration: "uncalibrated"`）
- ✅ SPEC-005 变更请求：注册新增 export_ref，评估 conditional hard export
- ✅ 单元测试：`tests/test_wyckoff.py`

### 16.4 不交付（全阶段）

- ❌ 支撑/阻力位自动计算（`key_levels.support/resistance` 始终为空数组）
- ❌ K 线形态识别（TA-Lib 有 61 种 CDL* 函数，但 MVP 不集成）
- ❌ 分钟线 / Tick 数据分析
- ❌ 多时间框架分析（日线 + 周线联动）
- ❌ 实时行情推送
- ❌ 涨跌停板对 VSA 的完整修正（P2 仅做 confidence 降级，见 §8.3）
- ❌ `metric://bid_ask_spread_proxy`（SPEC-004 §38 已注册，但全阶段不导出）
- ❌ LLM 生成的 summary（使用模板占位，与 Fundamentals 域一致）

---

*End of SPEC-014 v0.1.2*
