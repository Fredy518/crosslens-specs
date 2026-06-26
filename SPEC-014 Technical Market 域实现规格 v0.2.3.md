# SPEC-014：Technical/Market 域实现规格

**版本：** v0.2.3
**状态：** Review（Part I §1–§16）；Part II（§17–§28）Draft
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.7；SPEC-005 v0.2
**实现参考：** SPEC-013 v0.2.0（Adapter 映射、Evidence 边界、Pipeline 模式；非规范性上游）
**上游契约：**
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-004 §4 (Analysis Card 通用 Schema，含 ConstraintExport.registration_status)
- SPEC-004 §35-§40 (Technical/Market 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-005 §5 (Metric Registry)
**目标阶段：** 域实现规格 / MVP 实现前置

---

## 版本修订说明

### v0.2.3（全面审查 P2 闭环 — 格式/风格/参数澄清）

| 项 | 章节 | 修订 |
|:---:|---|---|
| P2 | §4.1.2 / §5.2 | STOCH 参数 `(14,3,0)` 澄清为 `STOCH(high, low, close, 14, 3, 3)`（Slow Stochastic） |
| P2 | §6.4 | Volume Classifier `None` 检查前置（对齐 §6.5 风格） |
| P2 | §9.3 | `divergence_assessment` 统一为字典 `.get()` 访问 |
| P2 | §11.4 | 原错位的 domain_payload-only 节移至 §11.3 之后，章节顺序 .0→.1→.2→.3→.4 连续 |
| P2 | §24.2.1 | 显式声明 Step 6 函数作用域内中间变量共享 |
| P2 | §25.3 | 修复 `rs_raw` 行双管道 Markdown 格式 |

### v0.2.2（审核复审 — Part II 集成语义 + P1/P2 设计补强）

关闭 SPEC-014 v0.2.1 审查报告 P0 #1/#2 及 P1/P2 建议项；**Part I（§1–§16）进入 Review**（Registry 已同步）；Part II（§17–§28）保持 Draft。上游 CR-014-001 已提交 SPEC-004 v0.2.7（`key_levels` + `threshold_calibration`）。

| 项 | 章节 | 修订 |
|:---:|---|---|
| P0 | §9.3 / §24.2 / §24.2.1 | 显式声明 P3+ clip + Phase 3 stance 映射延迟至 §24.2–§24.3 全部调整因子之后；§9.3 增加 forward reference |
| P0 | §24.2.1 | trending regime 下 `divergence_trend_conflict` 不计入 `signal_conflict`，消除 regime 门控与 `mixed` stance 语义冲突 |
| P1 | §16 | 正式定义 `P3★` 阶段标记（P3 批次 + Adapter 前置） |
| P1 | §19.6 | `regime_confidence` 引入 Hurst 样本量衰减因子 `min(1.0, (n−60)/120)` |
| P1 | §20.5 | 补充自校准 RS Rating 语义警告，防止 Playbook 误读为横截面排名 |
| P1 | §10.3 | 补充 P4 `key_levels` Breaking Change 对 Post-card Validation / Playbook Consumer 的影响分析 |
| P2 | 版本修订说明 | 注明 v0.2.0 变更已合并入 v0.2.1（Registry 无独立 v0.2.0 文件） |
| P2 | §24.3 | 讨论 Part I + Part II 调整因子累加风险与总预算设计约束（含 `adjustment_override` 告警） |

### v0.2.1（审核修订 — Part I P0 阻塞项 + 全文一致性修补）

在 v0.2.0 基础上关闭 SPEC-014 审核 P0/P1 项，**Part I（§1–§16）可进入 Review**；Part II（§17–§28）设计不变。

| 项 | 章节 | 修订 |
|:---:|---|---|
| P0 | §9.3 | 重写 stance 映射：`mixed` 在 Layer 1 方向冲突或背离-趋势矛盾时可产出；`neutral` 用于弱信号且无冲突 |
| P0 | §4.1.7 / §6.7 / §11.2 | `divergence_metrics` 增加 `divergence_strength` 字段，对齐 export `value_path`；增加 `obv_divergence_strength` 字段（对齐 §6.7 `obv_strength` 变量，修复定义缺失 Bug） |
| P0 | §7.4 | zone_bonus 规则拆分为 RSI/MACD/OBV 三分支，明确 MACD/OBV 无 zone bonus |
| P0 | §11.1 | 补全 7 个 registered export 的 evidence_ref + value_path 映射表（仿 SPEC-013 §4） |
| P1 | §9.5.0 | Part II Evidence 类型纳入 `_DOMAIN_EVIDENCE_TYPES` / `_OPTIONAL_EVIDENCE`；补充 EvidencePacket vs ConstraintExport 两层 `can_support_hard_constraint` 区分注释 |
| P1 | §24.1 / §24.2 | 修正交叉引用；`trend_direction` → `labels["trend"]` |
| P1 | §1.1.2 | 治理规则表补充 P3/P4 分阶段导出说明 |
| P1 | §10.1 | `threshold_calibration` 升级为子对象 `{part_i, part_ii}`；P0–P2 `part_ii=null`，P3+ `part_ii="self_calibrated_percentile"` |
| P1 | §10.3 | `threshold_calibration` 标注为 Breaking CR（SPEC-004 §37.2 升级为对象） |
| P1 | §16.3 / §17.3 / §18 | 澄清 Part I / Part II 校准策略分工；消除 `threshold_calibration` 字段值的矛盾表述 |
| P1 | §10.2 / §10.3 | 新增 domain_payload 扩展字段与 upstream CR 清单 |
| P1 | §12.2 / §13.6 | 同步 mixed/neutral 语义与契约测试 |
| P1 | §3 | Feature A/B/C/D/F 架构图补全阶段标注（P3/P3★/P3/P4/P4） |
| P1 | §25.3 | 注册候选表补充 `rs_raw`（建议保持 soft，附理由）；B 候选排序前置 |

### v0.2.0（高阶功能扩展）

> **发布说明：** v0.2.0 变更已合并入 v0.2.1 发布；Git / SPEC-REGISTRY 中无独立 v0.2.0 文件，修订内容见本节及 v0.2.1 变更表。

在 v0.1.2 的三层架构（Layer 1 指标 / Layer 2 背离 / Layer 3 威科夫）之上，新增 **Part II：高阶功能扩展（§17–§28）**，定义 5 项高阶能力，分阶段（P3–P4）交付：

| 代号 | 能力 | 维度补充 | 章节 | determinism | 数据 |
|:---:|---|---|:---:|---|---|
| **A** | 市场状态/机制识别 | 状态/元层（调制全局信号） | §19 | computed + structured | 现成（日线） |
| **B** | 相对强度与市场敏感度 | 横截面/相对 | §20 | computed | **需扩展 Adapter 指数数据（§26）** |
| **C** | 风险度量套件 | 风险/量化 | §21 | computed | 现成（日线） |
| **D** | 支撑阻力与成交量分布 | 价格点位（**解锁 `key_levels`**） | §22 | computed + structured | 现成（日线 + 量） |
| **F** | 多时间框架共振 | 时间 | §23 | computed | 现成（重采样） |

并新增 **§18 分位数自校准工具**（关闭 §14.1"阈值未校准"开放问题的横切方案）。

**设计立场：** A/C/D/F 与威科夫（Layer 3）、背离（Layer 2）"单序列、启发式、面向反转"的定位互补——它们分别补上**市场机制、风险、价格点位、时间**四个缺失维度；B 补上**横截面/相对**维度。

**治理一致性：** 所有新增 export 一律遵循 §11.0 / SPEC-004 §9.1 / SPEC-005 §6.4 的 `registration_status` 治理：首期以 `unregistered_mvp_local`（soft-only）交付，并向 SPEC-005 提交注册请求。其中 **C（风险度量）与 B（Beta / 相对回撤）经注册后是 Hard Constraint 的首选候选**（客观、确定性、对齐 SPEC-004 §35 #9 风险职责）。v0.1.2 的 §1–§16（P0–P2）内容不变。

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
| **P3** | 追加 §25.1 Part II A/B/C exports（soft-only，`unregistered_mvp_local`） | 不可 hard；经 SPEC-005 注册后升级 |
| **P4** | 追加 §25.2 Part II D/F exports（soft-only，`unregistered_mvp_local`） | 不可 hard；经 SPEC-005 注册后升级 |

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
5. 解释宏观或事件驱动催化的真实影响 → Macro/Meso、Event Driven 域

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

**高阶功能扩展（v0.2.0，Part II）对三层架构的补充：**

```text
Layer 0: 市场状态/机制层（元层，调制下游所有信号）   ← Feature A（§19，P3）
  └── Hurst 指数 + Kaufman 效率比率 + 波动率状态（分位自校准）

横切维度（不属于单一 Layer，与 Layer 1–3 并行）：
  ├── 相对强度层：RS 线 / RS Rating / Beta / Alpha          ← Feature B（§20，P3★）
  ├── 风险度量层：回撤 / 下行波动 / VaR / 风险调整收益       ← Feature C（§21，P3）
  ├── 价格点位层：成交量分布 POC/VA + 摆动枢轴聚类           ← Feature D（§22，P4）
  └── 时间维度层：日线→周线/月线多周期对齐                   ← Feature F（§23，P4）
```

- **Layer 0（市场状态）是元层**：先判定"当前是什么市场"，再据此调制 Layer 1–3 与 stance/confidence（§24.2 regime 门控）。
- **横切维度与 Layer 1–3 并行**，不改变 Layer 1→2→3 的单向数据流；它们各自从 Layer 1 输出与原始 OHLCV 取数。
- 详见 **Part II（§17–§28）**。

---

## 4. Evidence Packet 类型定义

Technical/Market 域计算 13 种 Evidence 指标组。其中 #1-#6 对应 SPEC-004 §36 已定义的 Evidence Packet 类型；#7-#8 为 v0.1.2 新增的域内计算类型；#9-#13 为 v0.2.0（Part II）新增的高阶功能 Evidence 类型（参见 §1.1 上游契约策略 + §17）。

| # | evidence_type | SPEC-004 注册 | TA-Lib 覆盖 | 自写逻辑 | 阶段 | 说明 |
|---|---|:---:|:---:|:---:|:---:|---|
| 1 | `moving_average_metrics` | ✅ | ✅ | — | P0 | 均线系统 |
| 2 | `momentum_metrics` | ✅ | ✅ | — | P0 | 动量指标 |
| 3 | `volatility_metrics` | ✅ | ✅ | — | P0 | 波动率指标 |
| 4 | `volume_metrics` | ✅ | ✅ | — | P0 | 成交量指标 |
| 5 | `liquidity_metrics` | ✅ | 部分 | 部分 | P0 | 流动性（需换手率数据） |
| 6 | `price_trend_metrics` | ✅ | ✅ | — | P0 | 趋势综合判断 |
| 7 | `divergence_metrics` | ❌ 新增 | ❌ | ✅ | P1 | 背离形态检测 |
| 8 | `wyckoff_metrics` | ❌ 新增 | ❌ | ✅ | P2 | 威科夫量价分析 |
| 9 | `regime_metrics` | ❌ 新增 | ❌ | ✅ | P3 | 市场状态/机制识别（Feature A，§19） |
| 10 | `relative_strength_metrics` | ❌ 新增 | 部分 | ✅ | P3 | 相对强度与 Beta（Feature B，§20） |
| 11 | `risk_metrics` | ❌ 新增 | 部分 | ✅ | P3 | 风险度量套件（Feature C，§21） |
| 12 | `support_resistance_metrics` | ✅（§36 #7） | ❌ | ✅ | P4 | 支撑阻力 + 成交量分布（Feature D，§22） |
| 13 | `multi_timeframe_metrics` | ❌ 新增 | ✅ | ✅ | P4 | 多时间框架共振（Feature F，§23） |

> **注：** `support_resistance_metrics`（SPEC-004 §36 #7 已列出）原不在 MVP 范围内，**v0.2.0 经 Feature D（§22）纳入 P4 实现**，并相应**解除 §10.1 对 `key_levels` 的置空约束**。`market_microstructure_metrics` 仍不在范围内，其 `bid_ask_spread_proxy` 亦不导出（参见 §16.2）。
>
> **#9–#13 的 Evidence 与共享池边界：** 与 #7–#8 一致，Part II 的新增 Evidence **不写入共享 Evidence Pool**（对齐 §4.0.1 / SPEC-013 §3 P0 边界），仅域内计算与组装 Card。

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
  stoch_k: float              # TA-Lib STOCH(high, low, close, 14, 3, 3) 的 slowk（Slow Stochastic %K）
  stoch_d: float              # TA-Lib STOCH(high, low, close, 14, 3, 3) 的 slowd（Slow Stochastic %D）
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
  obv_divergence_strength: float  # 0.0-1.0；OBV 背离强度（§7.4 仅 base_score + distance_bonus，无 RSI zone bonus）
  divergence_confirmations: int   # RSI + MACD + OBV 中确认背离的数量（0-3）。字段名为复数形式
  divergence_strength: float     # max(rsi_divergence_strength, macd_divergence_strength, obv_divergence_strength)；= §6.7 strongest_strength；export: metric://divergence_strength
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
| STOCH(14,3,3) | 17 | 30 | Slow Stochastic：`fastk=14, slowk=3, slowd=3`；warmup 14+3 日 |

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

> **阈值说明：** 0.005 = 5 日内变化 0.5%，约等于年化 25%。此阈值未经回测校准（参见 §14 开放问题）。在 `domain_payload.threshold_calibration.part_i` 中标注 `"uncalibrated"`。

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
IF volume_vs_20d_average is None:
    → "unknown"
ELIF volume_vs_20d_average > 2.0:
    → "abnormal_spike"
ELIF volume_vs_20d_average > 1.3:
    → "above_average"
ELIF volume_vs_20d_average < 0.7:
    → "below_average"
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

# Divergence Classifier 完成后 MUST 回写 Evidence metrics（供 §11.2 export）：
# divergence_metrics.divergence_strength = strongest_strength
# 注：rsi_strength = divergence_metrics.rsi_divergence_strength
#     macd_strength = divergence_metrics.macd_divergence_strength
#     obv_strength  = divergence_metrics.obv_divergence_strength（§4.1.7 存储字段）
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
  # RSI 背离：根据超买/超卖区位加分（极端区位的背离信号质量更高）
  IF indicator == "rsi":
    IF Regular Bullish AND rsi_first_trough < 30: +0.3
    ELIF Regular Bullish AND rsi_first_trough < 40: +0.15
    IF Regular Bearish AND rsi_first_peak > 70: +0.3
    ELIF Regular Bearish AND rsi_first_peak > 60: +0.15
    ELSE: +0.0
  
  # MACD 背离：无 zone bonus（无超买/超卖区位概念）
  IF indicator == "macd": +0.0
  
  # OBV 背离：无 zone bonus（成交量指标无超买/超卖区位）
  IF indicator == "obv": +0.0

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

# 背离和威科夫作为调整因子（divergence_assessment 为 §6.7 字典）
if divergence_assessment.get("has_regular_bullish"):
    raw_score += 0.15
if divergence_assessment.get("has_regular_bearish"):
    raw_score -= 0.15

if wyckoff_phase == "accumulation" and wyckoff_sub_phase in ("C", "D"):
    raw_score += 0.20
if wyckoff_phase == "distribution" and wyckoff_sub_phase in ("C", "D"):
    raw_score -= 0.20

# === Phase 2: 方向冲突检测（对齐 SPEC-004 §8.2 mixed = 正反证据都明显）===
def _classifier_sign(label: str) -> int:
    s = label_to_score.get(label, 0.0)
    if s > 0.2:
        return +1
    if s < -0.2:
        return -1
    return 0

bullish_dims = sum(1 for k in weights if _classifier_sign(labels[k]) > 0)
bearish_dims = sum(1 for k in weights if _classifier_sign(labels[k]) < 0)
layer1_conflict = bullish_dims >= 1 and bearish_dims >= 1

divergence_trend_conflict_raw = (
    labels["trend"] == "uptrend" and divergence_assessment.get("has_regular_bearish")
) or (
    labels["trend"] == "downtrend" and divergence_assessment.get("has_regular_bullish")
)

# P0–P2：无 regime_metrics，divergence_trend_conflict 即原始检测
divergence_trend_conflict = divergence_trend_conflict_raw
signal_conflict = layer1_conflict or divergence_trend_conflict

# === clip + Phase 3 stance 映射 ===
# P0–P2：在此立即 clip 并映射 stance（下方完整流程）
# P3+：clip 与 Phase 3 **延迟**至 §24.2 regime 门控 + §24.3 调整因子全部应用完毕后执行
#      signal_conflict 在 §24.2.1 按 regime 重新合成后再映射 stance

score = max(-1.0, min(1.0, raw_score))   # P3+ 时此行移至 §24.2.1 步骤 4

# === Phase 3: stance 映射（P3+ 在 §24.2.1 步骤 6 执行）===
# mixed：Layer 1 多维方向冲突，或趋势与 regular 背离矛盾，且综合 score 未强烈单边（|score| ≤ 0.5）
# neutral：|score| ≤ 0.2 且无 signal_conflict（信号弱、无显著矛盾）
# directional：score 超阈值且无 mixed 条件
IF signal_conflict and abs(score) <= 0.5:
    stance = "mixed"
ELIF score > 0.5:
    stance = "positive"
ELIF score > 0.2:
    stance = "moderately_positive"
ELIF score < -0.5:
    stance = "negative"
ELIF score < -0.2:
    stance = "moderately_negative"
ELIF abs(score) <= 0.2:
    stance = "neutral"
ELSE:
    # |score| > 0.5 但 signal_conflict 为 false 的残余路径（不应出现；防御性映射）
    stance = "positive" if score > 0 else "negative"
```

**边界值表（v0.2.1）：**

| 条件 | stance | opposing_evidence |
|------|--------|-------------------|
| `signal_conflict` 且 `|score| ≤ 0.5` | `mixed` | **必填**（§9.5.1 + §12.2） |
| `|score| ≤ 0.2` 且无 `signal_conflict` | `neutral` | 不要求 |
| `score > 0.5` 且无 mixed 条件 | `positive` | 必填 |
| `0.2 < score ≤ 0.5` 且无 mixed 条件 | `moderately_positive` | 必填 |
| 对称负面区间 | `negative` / `moderately_negative` | 必填 |

> **与 SPEC-013 的差异说明：** Fundamentals 将中间 score 带映射为 `mixed`；Technical 按 SPEC-004 §8.2 语义，**仅在有显式信号冲突时**产出 `mixed`，弱信号无冲突时用 `neutral`。

> **P3+ forward reference（§24.2.1）：** Part II 启用后，§9.3 的 `raw_score`（含背离/威科夫调整）在 **clip 之前**依次经 §24.2 regime 门控与 §24.3 Part II 调整因子调制；**clip 与 Phase 3 stance 映射延迟到全部调整因子应用完毕**。`divergence_trend_conflict` 在 trending regime 下不计入 `signal_conflict`（§24.2.1），避免 regime 已削弱背离意义时仍产出 `mixed`。

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
    confidence = min(confidence, 0.45)  # SPEC-004 AnalysisCard cap
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

Technical 域在域内创建 EvidencePacket 对象（对齐 SPEC-013 pipeline 模式），供 Card 组装时引用。Part I 固定 8 组；Part II（P3–P4）按 Feature 启用情况追加（见 `_OPTIONAL_EVIDENCE`）。

**evidence_id 命名规则：** `ev_tm_{type}_{run_id}`，其中 `{type}` 为 evidence_type 的缩写。

```python
# 域内 Evidence 创建（Step 2-4 + Part II Step 2A–2D 完成后）
_DOMAIN_EVIDENCE_TYPES = [
    # Part I（P0–P2）
    ("moving_average_metrics", "ma"),
    ("momentum_metrics",       "mom"),
    ("volatility_metrics",     "vol"),
    ("volume_metrics",         "volum"),
    ("liquidity_metrics",      "liq"),
    ("price_trend_metrics",    "trend"),
    ("divergence_metrics",     "div"),
    ("wyckoff_metrics",        "wyck"),
    # Part II（P3–P4，仅当对应 Feature 计算成功时追加）
    ("regime_metrics",              "regime"),
    ("relative_strength_metrics",   "rs"),
    ("risk_metrics",                "risk"),
    ("support_resistance_metrics",  "sr"),
    ("multi_timeframe_metrics",     "mtf"),
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
            # ── 两层区分 ──
            # EvidencePacket.can_support_hard_constraint（本字段）：标识该 Evidence 类型
            #   在原则上是否可支撑 Hard Constraint（取决于 determinism_level 和数据质量）。
            #   Layer 1 / Part II computed evidence = True；wyckoff/divergence = False。
            # ConstraintExport.can_support_hard_constraint（§11 / §25）：受 registration_status
            #   约束，`unregistered_mvp_local` 时 MUST be False（§17.3）。
            # 两者共同决定：EvidencePacket=True 是 hard 的必要不充分条件；
            #   实际能否 hard 还需 ConstraintExport.registration_status = "registered"。
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
# Layer 2/3 + Part II 为 optional：缺失不降级 domain_status，但记录在 evidence_coverage 中
_OPTIONAL_EVIDENCE = [
    "divergence_metrics",
    "wyckoff_metrics",
    # Part II（P3–P4）
    "regime_metrics",
    "relative_strength_metrics",
    "risk_metrics",
    "support_resistance_metrics",
    "multi_timeframe_metrics",
]
```

> **Part II Evidence 创建时机：** P0–P2 仅实例化 Part I 的 8 组。P3 起在 Step 2A–2C 成功后追加 regime / rs / risk；P4 在 Step 2D 追加 sr / mtf。未启用的 Feature **不得**创建空壳 EvidencePacket。

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

> **SPEC-004 §41 #7 对齐：** `neutral` 和 `unavailable` 不在 opposing_evidence 强制范围内。`mixed` 及所有 directional stance（`positive` / `moderately_positive` / `negative` / `moderately_negative`）**必须**有 opposing_evidence。Step 6 在 `signal_conflict` 时产出 `mixed`，§9.5.1 应从 Layer 1 负向分类器 + 矛盾背离自动填充 opposing。

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
  
  "threshold_calibration": {
    "part_i":  "uncalibrated",
    "part_ii": null
  },
  
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

> **key_levels 行为（P0–P3）：** 在 **Feature D（§22）启用前**，`support` 和 `resistance` **必须**为空数组 `[]`。若 Layer 3 检测到 Trading Range，`trading_range_high` / `trading_range_low` 可作为软参考（在 `wyckoff` 子对象中），**禁止**写入 `key_levels`。
>
> **key_levels 行为（P4 起，v0.2.0）：** Feature D 实现 `support_resistance_metrics` 后，**解除**置空约束——`key_levels` 改按 §22.6 的结构输出（仅当成功计算时非空，否则仍为 `[]`）。
>
> **契约测试约束：** P0–P3 阶段 `key_levels.support/resistance` **MUST** be `[]`。P4 起原约束由 `test_key_levels_empty_unless_sr_enabled` 取代（§27.4）：未启用 D 或数据不足 → `[]`；启用且成功 → 允许非空且 Level 结构合法。

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

### 10.3 上游变更请求清单（SPEC-004 CR）

以下扩展字段/结构在实现中使用，但 **SPEC-004 §37.2 尚未定义**。编码前以本 SPEC 为准；合并上游前 MUST 向 SPEC-004 提交变更请求：

| 变更项 | 类型 | 目标章节 | 阶段 | 说明 |
|---|---|---|:---:|---|
| `domain_payload.divergence` | 子对象 | SPEC-004 §37.2 | P1 | §10.1 结构 + §10.2 `strongest_type` 枚举 |
| `domain_payload.wyckoff` | 子对象 | SPEC-004 §37.2 | P2 | §10.1 结构 + §10.2 phase/sub_phase/vsa 枚举 |
| `domain_payload.threshold_calibration` | 子对象（Breaking） | SPEC-004 §37.2 | P0+ | **已提交 CR-014-001 → SPEC-004 v0.2.7** |
| `domain_payload.key_levels.source` / `.note` / P4 `[Level]` | schema 变更 | SPEC-004 §37.2–§37.4 | P0–P4 | **已提交 CR-014-001 → SPEC-004 v0.2.7**（P0–P3 空数组 + 元数据；P4 对象数组） |
| Evidence #7–#8 | evidence_type | SPEC-004 §36 | P1/P2 | `divergence_metrics` / `wyckoff_metrics` |
| Evidence #9–#13 | evidence_type | SPEC-004 §36 | P3/P4 | Part II 五组 Evidence |
| Part II export_ref | MetricRegistryEntry | SPEC-005 §5 | P3/P4 | §25.3 注册清单 |

> **P4 key_levels Breaking Change — 下游影响范围：**

| 下游 | 影响 | 必要动作 |
|---|---|---|
| SPEC-004 §37.2 schema | `support`/`resistance` 由 `[number]` 升级为 `[Level]` 对象数组（§22.6） | 提交 CR；更新 JSON Schema、示例与 `schema_version` |
| Post-card Validation（SPEC-004 §41） | 若 validator 仍按 `number[]` 校验，`Level` 结构 Card 会被 **block** | SPEC-004 增加 Level 字段校验（`price`/`strength`/`source`/`touches`）；P4 前 bump `schema_version` |
| Playbook Consumer（SPEC-006） | 直接索引 `key_levels.support[0]` 为数值的 soft 规则失效 | 迁移至 `support[0].price`；或改消费 `metric://nearest_support` / `metric://nearest_resistance` export |
| 契约测试（§13.6 / §27.4） | P0–P3 空数组约束与 P4 非空合法结构并存 | `test_key_levels_empty_unless_sr_enabled` + Level 结构强校验 |
| Conflict Detection（SPEC-004 §42） | 不直接读取 `key_levels`（读 stance / export / time_horizon） | 无直接影响 |
| Decision Trace / Observability | 仅记录 payload 快照 | 消费者需识别新结构，无 block 风险 |

> SPEC-004 §45（Post-card Validation MVP 范围）本身不定义 `key_levels` 类型——影响集中在 **§37.2 schema 校验器**与 **Playbook 对 payload 字段的直接引用**。P4 启用前 MUST 完成 SPEC-004 CR 合并，否则 Validation 与消费者按旧 schema 解析失败。

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

**P0 Export 完整映射（实现冻结，对齐 SPEC-013 §4 Metric Catalog）：**

| export_ref | evidence_type | evidence_id 模式 | value_path | determinism_level | registration_status | can_support_hard | allowed_constraint_types |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| `metric://rsi_14d` | `momentum_metrics` | `ev_tm_mom_{run_id}` | `rsi_14d` | computed | registered | true | `["hard", "soft"]` |
| `metric://price_above_50d_ma` | `moving_average_metrics` | `ev_tm_ma_{run_id}` | `price_above_50d_ma` | computed | registered | true | `["hard", "soft"]` |
| `metric://price_above_200d_ma` | `moving_average_metrics` | `ev_tm_ma_{run_id}` | `price_above_200d_ma` | computed | registered | true | `["hard", "soft"]` |
| `metric://volume_vs_20d_average` | `volume_metrics` | `ev_tm_volum_{run_id}` | `volume_vs_20d_average` | computed | registered | true | `["hard", "soft"]` |
| `metric://atr_14d` | `volatility_metrics` | `ev_tm_vol_{run_id}` | `atr_14d` | computed | registered | true | `["hard", "soft"]` |
| `metric://drawdown_from_52w_high` | `price_trend_metrics` | `ev_tm_trend_{run_id}` | `drawdown_from_52w_high` | computed | registered | true | `["hard", "soft"]` |
| `metric://average_dollar_volume_20d` | `liquidity_metrics` | `ev_tm_liq_{run_id}` | `average_dollar_volume_20d` | computed | registered | true | `["hard", "soft"]` |

> **Card 组装规则：** P0 `constraint_exports` **仅**包含上表 7 项；每项 `export_type = "metric"`，`evidence_ref` 指向对应 EvidencePacket，`value_path` 从该 Packet 的 `metrics` 字典读取。布尔型 metric（`price_above_*`）导出为 JSON boolean。

### 11.2 Layer 2 导出的 Metrics / Facts（P1 — soft-only）

背离检测依赖极值点参数（§7.2、§14.3），阈值未经 A 股回测校准。MVP 阶段**一律不支持 Hard Constraint**：

| export_ref | 说明 | registration_status | can_support_hard | allowed_constraint_types |
|---|---|:---:|:---:|:---:|
| `metric://divergence_confirmations` | 确认背离的指标数量 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://divergence_strength` | 最强背离的强度（§4.1.7 / §6.7 回写字段） | `unregistered_mvp_local` | false | `["soft"]` |
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

### 11.4 domain_payload-only 指标（未注册，不进 constraint_exports）

以下 Layer 1 指标在 Evidence / domain_payload 中计算，但 **MUST NOT** 进入 `constraint_exports`，直至 SPEC-005 注册：

| 字段（domain_payload） | 对应 export_ref（待注册） | 说明 |
|---|---|---|
| `atr_pct_14d` | `metric://atr_pct_14d` | ATR 百分比 |
| `macd_histogram` | `metric://macd_histogram` | MACD 柱值 |
| `adx_14d` | `metric://adx_14d` | ADX 14日 |
| `bb_position` | `metric://bb_position` | 布林带位置 |
| `amihud_illiquidity` | `metric://amihud_illiquidity` | Amihud 非流动性 |

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
      正常路径下 Step 6 在 signal_conflict 时产出 mixed，§9.5.1 应已填充 opposing；
      此路径仅覆盖 Card 组装后 evidence 检查仍发现 mixed 无 opposing 的边界情况）
    → 如果 stance 为 directional（positive/moderately_positive/negative/moderately_negative）：
      降级为 neutral，domain_status_reason = "no_opposing_evidence_for_directional_stance"
      warnings.append("directional_stance_no_opposing: 无足够反方证据支撑方向性判断，降级为 neutral")
```

> **注意：** `neutral` 不要求 `opposing_evidence`。Step 6 在 `|score| ≤ 0.2` 且无 `signal_conflict` 时产出 `neutral`。`mixed` 要求正反证据并存（§9.3 Phase 2–3），正常路径下 opposing 应由 §9.5.1 自动填充。

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
test_key_levels_must_be_empty            # key_levels.support/resistance MUST be [] (P0–P3；P4 起改名见 §27.4)
test_constraint_exports_registered_only   # P0: 仅 7 个 registration_status=registered hard exports
test_data_freshness_required_when_exports # constraint_exports 非空时 data_freshness 必填
test_time_horizon_bucket_populated       # time_horizon_bucket + days_min/max 必填
test_opposing_evidence_for_directional_stance  # §41 ¶7
test_stance_mixed_on_classifier_conflict      # §9.3 signal_conflict → mixed
test_stance_neutral_on_weak_no_conflict       # |score|≤0.2 且无 conflict → neutral
test_stance_mixed_requires_opposing           # mixed 时 opposing 非空（组装后）
test_divergence_strength_on_evidence_metrics  # §4.1.7 字段存在且 = strongest_strength
```

---

## 14. 开放问题

### 14.1 阈值校准

以下阈值均为经验值，未经 A 股回测验证。P0–P2 在 `domain_payload.threshold_calibration.part_i` 标注 `"uncalibrated"`（`part_ii = null`）。

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

| 方法 | 数据源 | 说明 | 阶段 |
|------|--------|------|:---:|
| `adapter.get_market_data()` | AlphaDB `stock_daily` | 日线 OHLCV | P0 |
| `adapter.get_market_data()` | AlphaDB `stock_dailybasic` | 估值 + 换手率 | P0 |
| `adapter.get_market_data()` | AlphaDB `stock_adj_factor` | 复权因子（待补充） | P0 |
| `adapter.get_index_data()` | AlphaDB `index_daily` | **基准指数日线（Feature B 前置，§26）** | P3 |

> **注：** Technical/Market 域 P0–P2 仅需日线行情数据，可在没有 AlphaDB 的情况下通过 TinyData 或其他数据源运行。**P3（Feature B 相对强度）新增对基准指数序列的依赖**（`get_index_data`，§26），作为 P3 前置条件；该方法不可用时 B 段降级，不影响 A/C/D/F。
>
> **Python 依赖：** Part II 不引入新的第三方依赖——Hurst/VaR/回归用 `numpy`，重采样用 `pandas`，枢轴检测复用 §15.1 已有的 `scipy.signal.find_peaks`。

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

> **分阶段交付：** P0 = 实现冻结范围（必须先完成并通过契约测试）；P1/P2 = Part I 后续增量；**P3–P4 = Part II 高阶功能扩展（§17–§28）**（原 P5 已合并入 P3）。算法章节（§7–§8、§19–§23）保留完整设计，但实现可按阶段裁剪。

**阶段标记约定：** P0–P4 为交付批次。`P3★` 表示 **P3 批次内交付、但需 Adapter 前置工作**（§26 `get_index_data()` 基准指数数据）；可与 Feature A/C 并行推进，**不得**在前置条件完成前启动。

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
- ✅ Layer 2/3 参数与 §6 分类器阈值的 A 股分布回测验证（§14.1）；`domain_payload.threshold_calibration.part_i` 保持 `"uncalibrated"`（Part I 迁移见 §28.5；P3 起 `part_ii` 字段升级为 `"self_calibrated_percentile"`，§17.3）
- ✅ SPEC-005 变更请求：注册新增 export_ref，评估 conditional hard export
- ✅ 单元测试：`tests/test_wyckoff.py`

### 16.4 P3 — 市场状态 + 相对强度 + 风险度量（Part II，P2 完成后）

> **前置条件：** 先实现 §26 `get_index_data()` Mock 桩，再并行推进 A/B/C。

- ✅ §18 分位数自校准工具（`calibration.py`）
- ✅ Feature A 市场状态/机制识别（Hurst + ER + 波动率状态，§19）→ `regime_metrics`
- ✅ **Feature B 相对强度与 Beta**（RS 线 / RS Rating / Mansfield / Beta / Alpha / 相对回撤，§20）→ `relative_strength_metrics`（Adapter `get_index_data()` P3 前置，§26）
- ✅ Feature C 风险度量套件（回撤 / VaR-CVaR / 风险调整 / ATR 止损，§21）→ `risk_metrics`
- ✅ regime 门控 + stance/confidence 调整（§24.2/§24.4）
- ✅ §25.1 soft-only exports；§25.3 SPEC-005 注册请求（`beta_252d`、`relative_drawdown`、风险度量 hard 候选）→ **已注册**（`metrics_registry.py` + `tests/test_metrics_registry.py`，§25.3）
- ✅ 单元测试：`tests/test_calibration.py`、`tests/test_regime.py`、`tests/test_relative_strength.py`、`tests/test_risk.py`

### 16.5 P4 — 支撑阻力 + 多时间框架（P3 完成后）

- ✅ Feature D 支撑阻力 + 成交量分布（§22）→ `support_resistance_metrics`，**解锁 `key_levels`**（§10.1 / §22.6）
- ✅ Feature F 多时间框架共振（日/周/月，§23）→ `multi_timeframe_metrics`
- ✅ §25.2 soft-only exports
- ✅ 契约测试更新：`test_key_levels_empty_unless_sr_enabled`（替换 §13.6 的 `test_key_levels_must_be_empty`）
- ✅ 单元测试：`tests/test_levels.py`、`tests/test_mtf.py`

### 16.6 不交付（全阶段）

- ❌ 筹码分布 / 成本分布（Feature E，未纳入本轮）
- ❌ 资金流向 / 北向资金 / 龙虎榜（Feature G，需更大数据契约扩展，未纳入本轮）
- ❌ K 线 / 图表形态识别（Feature H，TA-Lib CDL* 等，未纳入本轮）
- ❌ 横截面 IBD 1–99 RS Rating（需全市场快照，§28.3）
- ❌ 分钟线 / Tick 数据分析
- ❌ 实时行情推送
- ❌ 涨跌停板对 VSA 的完整修正（P2 仅做 confidence 降级，见 §8.3）
- ❌ `metric://bid_ask_spread_proxy`（SPEC-004 §38 已注册，但全阶段不导出）
- ❌ 参数化波动率预测（GARCH 等，§28.4）
- ❌ LLM 生成的 summary（使用模板占位，与 Fundamentals 域一致）

> **范围变更说明（v0.2.0）：** "支撑/阻力位自动计算"与"多时间框架分析"在 v0.1.2 曾列为"全阶段不交付"，**v0.2.0 经 Feature D / F 分别纳入 P4**。

---

# Part II：高阶功能扩展（v0.2.0 / P3–P4）

> 本部分（§17–§28）定义 5 项高阶能力 A/B/C/D/F。Part I（§1–§16）描述 P0–P2 的三层基础架构；Part II 在其上叠加**市场机制（Layer 0）**与**相对、风险、点位、时间**四个横切维度。所有算法的确定性部分仍应全部可单元测试（对齐 §1 文档目标）。

## 17. 高阶功能扩展总览

### 17.1 互补定位：六维度框架

威科夫（§8）与背离（§7）是**单序列、启发式、面向反转/结构**的软信号。它们覆盖了"价格与成交量的形态"，但留下了五个未覆盖的分析维度。Part II 按维度补全：

| 维度 | 由谁覆盖 | 缺口与 Part II 的补全 |
|---|---|---|
| 形态/结构 | 威科夫（L3）、背离（L2） | 已覆盖 |
| **横截面/相对** | — | **B（§20，P3★）**：相对指数/行业是强还是弱？（个股不孤立交易） |
| **市场机制** | — | **A（§19，P3）**：当前是趋势市还是震荡市？哪类工具此刻有效？ |
| **风险/量化** | — | **C（§21，P3）**：回撤、下行波动、尾部风险、该下多大注 |
| **价格点位** | trading_range（弱） | **D（§22，P4）**：有成交量背书的支撑/阻力（解锁 key_levels） |
| **时间** | — | **F（§23，P4）**：大周期（周/月线）方向是否与日线一致 |

### 17.2 分阶段交付（P3–P4）

延续 Part I 的实现冻结策略，Part II 按**价值优先**排序——**B 价值最高，与 A/C 同属 P3**：

| 阶段 | 内容 | 数据依赖 | 关键产出 |
|:---:|---|---|---|
| **P3** | §18 自校准 + A 市场状态（§19）+ **B 相对强度（§20）** + C 风险度量（§21） | 日线 + **指数基准（§26，P3 前置）** | 横截面/相对、机制、风险——可注册 hard 的核心扩展 |
| **P4** | D 支撑阻力（§22）+ F 多时间框架（§23） | 现成日线 | 价格点位（解锁 key_levels）+ 时间维度 |

> **排序理由（v0.2.0 修订）：** B 价值最高，应尽早交付。其唯一额外依赖是基准指数序列（`get_index_data()`），作为 **P3 前置条件**提前实现（§26），与 A/C 并行交付。P5 层取消——原 P5 内容已并入 P3。各阶段独立可交付，缺失高阶 Evidence 不降级 `domain_status`（与 Layer 2/3 一致，列入 `_OPTIONAL_EVIDENCE`，§9.5.0）。

### 17.3 治理与 determinism 总则

| 原则 | 规则 |
|---|---|
| 初始注册状态 | 所有 Part II 新增 export **首期** `registration_status = "unregistered_mvp_local"`，`can_support_hard_constraint = false`，`allowed_constraint_types = ["soft"]`（受 SPEC-004 §9.1 `ConstraintExport` 校验器强制）。 |
| 注册升级路径 | 向 SPEC-005 提交 `MetricRegistryEntry` 注册请求（§25.3）；注册完成后升级为 `registered`，方可参与 Hard Constraint。 |
| Hard 候选 | **B 的 `beta_252d` / `relative_drawdown`** 与 **C 的风险度量**（`max_drawdown_1y`、`hist_var_95_1y` 等）是注册后的 Hard Constraint 首选（客观、确定性、对齐 SPEC-004 §35 #9）。 |
| determinism 标注 | 连续数值（Hurst、ER、Beta、VaR、POC 价位）为 `computed`；离散标签（regime、risk_state、rs_state）含阈值判断，为 `structured`。 |
| 阈值校准 | 离散标签**一律基于 §18 分位数自校准**，而非写死全局阈值；P3 启用后 `domain_payload.threshold_calibration` 升级为子对象：`{"part_i": "uncalibrated", "part_ii": "self_calibrated_percentile"}`（§10.3 Breaking CR；P0–P2 仍为 `{"part_i": "uncalibrated", "part_ii": null}`）。 |

### 17.4 共享数据流

```text
原始 OHLCV + adj_factor (Step 1)
   │
   ├─→ Layer 1 指标 (Step 2) ─────────────┐
   │                                       │
   ├─→ §18 分位自校准基线（rolling 分布）   │
   │                                       ▼
   ├─→ A 市场状态 (Layer 0) ──── 调制 ──→ stance/confidence（§24.2）
   ├─→ C 风险度量 ←── ATR/log_returns（复用 Layer 1）
   ├─→ D 支撑阻力 ←── find_peaks（复用 Layer 2 摆动检测）+ 成交量分布
   ├─→ F 多时间框架 ←── 重采样 OHLCV → 周/月线 → 复用 Layer 1
   └─→ B 相对强度 ←── 个股 close + 基准指数 close（§26 新数据）
```

> Part II **复用** Part I 的两块基础设施：(1) Layer 1 的 TA-Lib 指标与 log 收益率；(2) Layer 2 背离检测的 `find_peaks` 摆动点检测（D 的枢轴聚类直接复用）。

---

## 18. 分位数自校准工具（横切，缓解 Part II 的 §14.1 阈值问题）

### 18.1 动机

§14.1 列出 Part I 全部分类器阈值"未经 A 股回测校准"。业界对市场状态/波动率/相对强度类标签的最佳实践是**用每个标的自身的历史分布做分位排名**，而非写死全局阈值（如 `ADX>25`）——后者在不同标的、不同时期会静默漂移。Part II 的所有离散标签 **MUST** 基于本节工具产出。

> **与 §14.1 的关系（v0.2.1 澄清）：** 本节**不关闭** Part I §6 固定阈值问题；Part I 仍通过 `threshold_calibration.part_i = "uncalibrated"` 标注（直至 §28.5 迁移）。本节关闭的是 **Part II 新增标签** 的未校准问题：P3 起将 `threshold_calibration.part_ii` 设为 `"self_calibrated_percentile"`。

### 18.2 工具定义

```python
def rolling_percentile(
    series: np.ndarray,      # 历史值序列（升序，含当前值）
    value: float,            # 待定位的当前值
    lookback: int = 252,     # 回看窗口（约 1 年交易日）
    min_samples: int = 60,   # 最小有效样本，不足返回 None
) -> float | None:
    """返回 value 在最近 lookback 窗口分布中的分位（0.0–1.0）。"""
    window = series[-lookback:]
    valid = window[~np.isnan(window)]
    if len(valid) < min_samples:
        return None
    return float(np.sum(valid <= value) / len(valid))


def percentile_to_bucket(
    pct: float | None,
    bounds: tuple[float, float, float] = (0.20, 0.80, 0.95),
    labels: tuple[str, str, str, str] = ("low", "normal", "high", "extreme"),
) -> str:
    """分位 → 四档标签。pct=None → labels 外的 'unknown'。"""
    if pct is None:
        return "unknown"
    lo, hi, ext = bounds
    if pct < lo:    return labels[0]
    if pct < hi:    return labels[1]
    if pct < ext:   return labels[2]
    return labels[3]
```

### 18.3 应用约定

| 约定 | 规则 |
|---|---|
| determinism | `rolling_percentile` 输出为 `computed`（给定窗口确定）；`percentile_to_bucket` 的标签为 `structured`（含 bounds 参数）。 |
| 样本不足 | `< min_samples` 返回 `None` → 标签 `"unknown"` → 该信号不参与 stance 调制，并记 `warnings.append("self_calibration_insufficient_history")`。 |
| 窗口口径 | 默认 `lookback=252`（1 年）；regime 用 `lookback=252`，风险百分位用 `lookback=504`（2 年，覆盖更长尾部），各 Feature 在其章节声明。 |
| 标注 | P3 启用后将 `domain_payload.threshold_calibration.part_ii` 设为 `"self_calibrated_percentile"`；Part I 的 `.part_i` 字段保持 `"uncalibrated"` 直至 §28.5 迁移。 |

> **与 Part I 的关系：** Part I 的 §6 分类器阈值保持原状（不破坏 P0–P2 冻结），但 §14.1 的校准建议路径在 Part II 中以本工具落地。后续可将 Part I 分类器逐步迁移到自校准（列为 §28 开放项）。

---

## 19. Feature A：市场状态 / 机制识别（Layer 0，P3）

### 19.1 概览

市场状态层是**调制所有下游信号的元层**：先判定"当前价格行为属于哪种机制"，再据此调整 stance 权重与 confidence（§24.2）。核心论点——**误判市场机制是代价最高的分析错误**：趋势工具用在均值回归市场会反复亏损，反之亦然。

```text
输入: close（前复权）, Layer 1 的 hist_vol_20d 序列
三个正交度量:
  1. Hurst 指数 H        → 持续性（趋势 vs 均值回归）
  2. Kaufman 效率比率 ER  → 趋势"干净"程度（0=纯噪音, 1=完美直线）
  3. 波动率分位（§18）    → 与趋势/震荡正交的第二维度
合成: regime（trending / mean_reverting / random）× volatility_regime（low..extreme）
```

### 19.2 Evidence：regime_metrics

```text
evidence_type: "regime_metrics"
generation_type: computed
determinism_level: structured    # 连续度量为 computed，但 regime 标签含阈值
can_support_hard_constraint: false
数据来源: stock_daily (close) + Layer 1 hist_vol_20d

metrics:
  hurst_exponent: float | None      # R/S 法，0.0–1.0；样本不足为 None
  efficiency_ratio: float           # Kaufman ER，0.0–1.0
  realized_vol_percentile: float | None  # hist_vol_20d 在 252 日分布中的分位（§18）
  trend_direction: str              # "up" | "down" | "none"（基于 ma_50d_slope 符号）
  regime: str                       # "trending" | "mean_reverting" | "random" | "unknown"
  volatility_regime: str            # "low" | "normal" | "high" | "extreme" | "unknown"
  regime_confidence: float          # 0.0–1.0，见 §19.6
  regime_persistence_days: int      # 当前 regime 已持续的交易日数
```

### 19.3 Hurst 指数（R/S 重标极差法）

```python
def hurst_rs(series: np.ndarray, min_chunk: int = 8, max_chunks: int = 8) -> float | None:
    """对数价格序列的 Hurst 指数（rescaled range / R/S 分析）。"""
    log_price = np.log(series[~np.isnan(series)])
    n = len(log_price)
    if n < 64:                      # 数据过短无法稳健估计
        return None
    # 取多种子区间长度，对每种长度计算平均 R/S
    chunk_sizes = np.unique(np.floor(
        np.logspace(np.log10(min_chunk), np.log10(n // 2), max_chunks)
    ).astype(int))
    rs_means, ns = [], []
    for size in chunk_sizes:
        rs_vals = []
        for start in range(0, n - size + 1, size):
            chunk = log_price[start:start + size]
            incr = np.diff(chunk)
            if len(incr) < 2 or np.std(incr) == 0:
                continue
            mean_incr = np.mean(incr)
            cumdev = np.cumsum(incr - mean_incr)
            R = np.max(cumdev) - np.min(cumdev)
            S = np.std(incr)
            rs_vals.append(R / S)
        if rs_vals:
            rs_means.append(np.mean(rs_vals)); ns.append(size)
    if len(ns) < 3:
        return None
    # log(R/S) = H * log(n) + c  → 斜率即 H
    H = np.polyfit(np.log(ns), np.log(rs_means), 1)[0]
    return float(np.clip(H, 0.0, 1.0))
```

**判定（自校准优先，回退经典阈值）：**

```text
IF hurst is None:              persistence = "unknown"
ELIF hurst > 0.55:             persistence = "trending"        # 持续性强
ELIF hurst < 0.45:             persistence = "mean_reverting"  # 反持续
ELSE:                          persistence = "random"          # 随机游走
```

> **参数：** `lookback = 252` 个交易日（约 1 年）。Hurst 在短窗口下方差大，**MUST** 要求 ≥ 64 个有效样本，否则 `hurst_exponent = None`。

### 19.4 Kaufman 效率比率（趋势干净度）

```python
def efficiency_ratio(close: np.ndarray, period: int = 20) -> float:
    direction = abs(close[-1] - close[-period - 1])
    volatility = np.sum(np.abs(np.diff(close[-period - 1:])))
    return float(direction / volatility) if volatility > 0 else 0.0
```

ER 接近 1 = 单边干净趋势；接近 0 = 来回震荡。用于在 `trending` 内区分强弱、并作为 regime_confidence 的输入。

### 19.5 波动率状态（自校准）

```python
# 复用 Layer 1 的 hist_vol_20d 序列（§4.1.3），按 §18 取分位
vol_pct = rolling_percentile(hist_vol_20d_series, hist_vol_20d_series[-1], lookback=252)
volatility_regime = percentile_to_bucket(vol_pct, bounds=(0.25, 0.75, 0.95))
```

> 波动率是与趋势/震荡**正交**的维度——"平静趋势"与"剧烈趋势"是完全不同的交易环境，因此独立成维而非并入 regime。

### 19.6 regime 合成判定

```python
def determine_regime(hurst, er, vol_regime, ma_50d_slope, n: int) -> RegimeAssessment:
    # n = Hurst 输入序列的有效样本量（§19.3 lookback 内非 NaN 交易日数）
    # 方向
    if ma_50d_slope > 0.005:    direction = "up"
    elif ma_50d_slope < -0.005: direction = "down"
    else:                       direction = "none"

    # 机制（Hurst 主轴，ER 辅助）
    if hurst is None:
        regime = "unknown"
    elif hurst > 0.55 and er > 0.3:
        regime = "trending"
    elif hurst < 0.45:
        regime = "mean_reverting"
    else:
        regime = "random"

    # 置信度：Hurst 偏离 0.5 的幅度 + ER 一致性 + 样本量衰减
    if hurst is None:
        confidence = 0.0
    else:
        hurst_strength = min(abs(hurst - 0.5) / 0.2, 1.0)   # 0.5→0, 0.7/0.3→1
        er_align = er if regime == "trending" else (1 - er)
        sample_decay = min(1.0, max(0.0, (n - 60) / 120))   # 64→~0.03, 180→1.0
        confidence = round((0.6 * hurst_strength + 0.4 * er_align) * sample_decay, 2)

    return RegimeAssessment(regime, direction, vol_regime, confidence)
```

> **样本量衰减：** Hurst R/S 法在 64 样本时方差极大，与 252 样本下相同 H 值可靠性不同。`sample_decay` 使 `regime_confidence` 在短窗口下自动压低，避免 Playbook 对低样本 regime 标签过度信任。

### 19.7 数据要求

| 度量 | 最少 | 推荐 | 说明 |
|---|:---:|:---:|---|
| Hurst | 64 | 252 | < 64 → `None`，regime 退化为 `unknown` |
| ER | period+1 | 60 | 复用 close |
| 波动率分位 | 60 | 252 | 复用 Layer 1 hist_vol_20d；§18 |

### 19.8 constraint_exports（P3，soft-only）

| export_ref | 说明 | registration_status | can_support_hard | allowed |
|---|---|:---:|:---:|:---:|
| `metric://hurst_exponent` | Hurst 指数 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://efficiency_ratio` | Kaufman ER | `unregistered_mvp_local` | false | `["soft"]` |
| `label://market_regime` | 市场机制标签 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://regime_is_trending` | 是否趋势市 | `unregistered_mvp_local` | false | `["soft"]` |

> **注册请求（§25.4）：** Hurst、ER 为确定性连续值，拟提交 SPEC-005 注册为 `computed` metric。注册后仍建议保持 soft（regime 是上下文，不应单独构成硬性禁入/准入），但可被 Playbook soft 规则与 §24.2 门控引用。

---

## 20. Feature B：相对强度与市场敏感度（横切，P3★）

### 20.1 概览

个股从不孤立交易。"个股涨 10% 但大盘涨 20%"实为**弱势**——这是 Layer 1–3 全部单序列分析永远看不到的维度。本特性对标基准（大盘 / 行业），产出相对强弱与系统性风险（Beta）。

> **对基本面投资者的价值：** 强基本面 + **弱 RS** = 价值陷阱 / 时机未到；强基本面 + **强 RS** = 市场开始认同论点。这是 Technical 域为基本面"印证 / 择时"的核心贡献。

### 20.2 数据契约扩展（P3 前置条件，详见 §26）

B 需要**基准指数日线序列**，当前 Adapter 未提供。**§26 的 `get_index_data()` 实现是 P3 的前置工作**，应在 A/B/C 其他模块并行启动前完成（可优先做 Mock 桩解锁单测，AlphaDB 实现后接入集成测试）。新增方法：

```python
def get_index_data(index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """基准指数日线。列: trade_date, close（按 trade_date 升序）。"""
```

**基准解析规则（benchmark resolution）：**

| 优先级 | 基准 | index_code 来源 |
|:---:|---|---|
| 1（市场） | 沪深300 | `000300.SH`（默认市场基准） |
| 2（行业，可选） | 申万一级行业指数 | 由 `get_industry_peers` 所属行业映射（§26.2） |
| 降级 | 无指数数据 | `relative_strength_metrics` 不产出，记 `warnings.append("benchmark_unavailable")`，B 段 Evidence 标 optional 缺失 |

对齐时按 `trade_date` 内连接（交易日对齐），个股与基准取交集日期。

### 20.3 Evidence：relative_strength_metrics

```text
evidence_type: "relative_strength_metrics"
generation_type: computed
determinism_level: computed       # 全部为确定性回归/比值
can_support_hard_constraint: false  # MVP 未注册；beta/相对回撤为注册后 hard 候选
数据来源: stock_daily(close) + get_index_data(benchmark close)

metrics:
  benchmark_code: str               # 实际使用的基准（如 000300.SH）
  rs_raw: float                     # 加权 ROC（§20.5）
  relative_strength_percentile: float | None  # rs_raw 在自身 252 日分布中的分位（§18）
  rs_line_slope_20d: float          # RS 线（close/index）20 日斜率
  mansfield_rs: float               # Mansfield 相对表现（§20.4）
  beta_252d: float | None           # 对基准的 Beta（OLS，§20.6）
  alpha_252d: float | None          # 年化 Alpha（截距×252）
  relative_return_60d: float        # 个股 60 日收益 − 基准 60 日收益
  relative_drawdown: float          # 个股回撤 − 基准回撤（同期）
  rs_state: str                     # "leader" | "in_line" | "laggard" | "unknown"
```

### 20.4 RS 线与 Mansfield RS

```python
rs_ratio = close / index_close                       # 标准 RS 比值（逐日）
rs_line_slope_20d = (rs_ratio[-1] - rs_ratio[-21]) / rs_ratio[-21]
# Mansfield 相对表现：RS 比值偏离其 200 日均线的程度（零线穿越识别强弱反转）
mansfield_rs = (rs_ratio[-1] / sma(rs_ratio, 200)[-1] - 1) * 100
```

RS 线斜率 > 0 = 跑赢基准；Mansfield 上穿零线 = 由弱转强。

### 20.5 RS Rating（加权 ROC，近端加权）

```python
def rs_raw(close: np.ndarray) -> float:
    """IBD 式加权 ROC：近一季度权重最高。需 ≥ 252 日。"""
    roc = lambda n: (close[-1] / close[-n - 1] - 1)
    return 0.4 * roc(63) + 0.2 * roc(126) + 0.2 * roc(189) + 0.2 * roc(252)
```

> **单股 vs 横截面：** IBD 的 1–99 RS Rating 需对**全市场横截面**做分位排名，单股分析时无全市场快照。MVP 采用**自校准**：`relative_strength_percentile = rolling_percentile(rs_raw_history, rs_raw_now, lookback=252)`（§18），衡量"相对自身历史是否处于强势"。真正的横截面 1–99 Rating 需批量/选股上下文，列为 §28 开放项。

> **⚠ 语义警告（Playbook 消费者）：** 上述自校准分位衡量的是"相对**自身历史**是否走强"，**不是** IBD 式"相对**全市场**排名"。持续弱势股在"没那么弱"时仍可能获得高分位——表示**边际改善**，不等于**市场领先**。Playbook 规则 **不得**将 `relative_strength_percentile > 0.8` 直接等同于 leader；应结合 §20.7 `rs_state` 与 `relative_return_60d` / `mansfield_rs`。横截面 Rating 见 §28.3。

### 20.6 Beta / Alpha（OLS 回归）

```python
def beta_alpha(stock_ret: np.ndarray, bench_ret: np.ndarray) -> tuple[float, float]:
    """对齐后的日对数收益回归：stock_ret = alpha + beta * bench_ret。"""
    if len(stock_ret) < 120 or np.var(bench_ret) == 0:
        return None, None
    beta = np.cov(stock_ret, bench_ret)[0, 1] / np.var(bench_ret)
    alpha_daily = np.mean(stock_ret) - beta * np.mean(bench_ret)
    return float(beta), float(alpha_daily * 252)   # alpha 年化
```

> **Beta 是 Hard Constraint 首选候选**：客观、确定性，可表达"组合 Beta 上限""高 Beta 标的在高波动 regime 下降权"等风险约束（注册后，§25.4）。

### 20.7 RS 状态判定

```text
# 综合 rs_line_slope、relative_return_60d、mansfield_rs
IF benchmark_unavailable:               rs_state = "unknown"
ELIF relative_return_60d > 0 AND mansfield_rs > 0 AND rs_line_slope_20d > 0:
    rs_state = "leader"                  # 多维确认跑赢
ELIF relative_return_60d < 0 AND mansfield_rs < 0:
    rs_state = "laggard"                 # 跑输
ELSE:
    rs_state = "in_line"                 # 与基准同步
```

### 20.8 数据要求

| 度量 | 最少 | 推荐 | 说明 |
|---|:---:|:---:|---|
| rs_raw / RS Rating | 253 | 280 | 需 252 日 ROC |
| Beta / Alpha | 120 | 252 | OLS 稳健性 |
| RS 线 / Mansfield | 200 | 250 | Mansfield 需 200 日均线 |

### 20.9 constraint_exports（P3；beta_252d / relative_drawdown 已注册为 hard）

| export_ref | 说明 | registration_status | can_support_hard | allowed |
|---|---|:---:|:---:|:---:|
| `metric://rs_raw` | 加权 ROC 相对强度 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://beta_252d` | 对基准 Beta | `registered` | true | `["hard","soft"]` |
| `metric://relative_drawdown` | 相对回撤 | `registered` | true | `["hard","soft"]` |
| `label://rs_state` | 相对强弱标签 | `unregistered_mvp_local` | false | `["soft"]` |

> **已注册（§25.3）：** `beta_252d`、`relative_drawdown` 已注册为 `computed` 且 `can_support_hard_constraint = true`，作为风险/择时类 Hard Constraint 载体（实现：`metrics_registry.py`）。

---

## 21. Feature C：风险度量套件（横切，P3）

### 21.1 概览

SPEC-004 §35.1 #9（风险回撤）是 Technical 域的**授权职责**，但 Part I 仅有一个 `drawdown_from_52w_high`。本特性把它升级为体系化风险层，也是 §39 `liquidity_risk`（high 严重度）冲突类型的直接支撑。

> **设计立场：** 风险指标客观、确定性强（纯 `computed`、仅用日线），是**最适合 Hard Constraint 的一类**（"最大可接受回撤""组合 Beta 上限""最低流动性"）。与方向无关——威科夫/背离给方向，本套件给"该不该下注、下多大、止损在哪"。

### 21.2 Evidence：risk_metrics

```text
evidence_type: "risk_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: false   # MVP 未注册；注册后多项升级为 hard（§25.4）
数据来源: stock_daily (close, high, low) + Layer 1 (atr_14d)

metrics:
  # 回撤
  current_drawdown: float           # 距滚动峰值的回撤（≤ 0）
  max_drawdown_1y: float            # 近 252 日最大回撤（≤ 0）
  underwater_days: int              # 距上一峰值的交易日数
  ulcer_index_1y: float             # 回撤深度的 RMS（下行痛苦度）
  # 下行风险
  downside_deviation_ann: float     # 负收益年化半标准差
  hist_var_95_1y: float             # 历史 VaR（日，5% 分位，≤ 0）
  hist_cvar_95_1y: float            # 历史 CVaR / 期望损失（≤ 0）
  max_single_day_loss_1y: float     # 近 1 年单日最大跌幅
  # 风险调整收益
  annualized_return_1y: float
  annualized_vol_1y: float
  sharpe_like_1y: float             # 年化收益 / 年化波动（rf=0）
  sortino_1y: float                 # 年化收益 / 下行波动
  calmar_1y: float                  # 年化收益 / |最大回撤|
  # 可执行风险参考
  atr_stop_long: float              # close − k×ATR（默认 k=3）
  atr_stop_pct: float               # (close − atr_stop_long) / close
  risk_state: str                   # "low" | "moderate" | "elevated" | "high" | "unknown"
```

### 21.3 回撤分析

```python
def drawdown_analytics(close: np.ndarray, lookback: int = 252) -> dict:
    px = close[-lookback:]
    running_peak = np.maximum.accumulate(px)
    dd = px / running_peak - 1.0                       # 逐日回撤（≤ 0）
    current_drawdown = float(dd[-1])
    max_drawdown_1y = float(np.min(dd))
    last_peak_idx = int(np.argmax(running_peak == px)) # 最近一次创新高的位置
    underwater_days = int(len(px) - 1 - np.where(px == running_peak)[0][-1])
    ulcer_index = float(np.sqrt(np.mean((dd * 100) ** 2)))
    return {...}
```

### 21.4 下行风险

```python
log_ret = np.diff(np.log(close[-253:]))               # 近 1 年日对数收益
downside = log_ret[log_ret < 0]
downside_deviation_ann = float(np.std(downside) * np.sqrt(252)) if len(downside) else 0.0
# 历史法 VaR / CVaR（不假设正态）
hist_var_95 = float(np.percentile(log_ret, 5))        # 5% 分位（≤ 0）
hist_cvar_95 = float(np.mean(log_ret[log_ret <= hist_var_95]))
max_single_day_loss = float(np.min(log_ret))
```

> **历史法 vs 参数法：** A 股日收益尖峰厚尾、且有涨跌停截断，**MUST** 用历史分位法而非正态参数法（避免低估尾部）。调研亦表明 regime-aware / 历史法对左尾估计更稳健。参数化 GARCH 列为 §28 开放项。

### 21.5 风险调整收益

```python
ann_ret = float(np.mean(log_ret) * 252)
ann_vol = float(np.std(log_ret) * np.sqrt(252))
sharpe_like = ann_ret / ann_vol if ann_vol > 0 else 0.0
sortino    = ann_ret / downside_deviation_ann if downside_deviation_ann > 0 else 0.0
calmar     = ann_ret / abs(max_drawdown_1y) if max_drawdown_1y < 0 else 0.0
```

### 21.6 ATR 止损与仓位参考

```python
atr_stop_long = float(close[-1] - 3.0 * atr_14d)      # 复用 Layer 1 ATR
atr_stop_pct  = float((close[-1] - atr_stop_long) / close[-1])
```

> 仅作**参考点位**（非交易指令），供 Playbook/用户做仓位与止损参考；`k` 默认 3.0，可配置。

### 21.7 risk_state 判定（自校准）

```python
# 用波动率分位 + 回撤幅度合成（§18），避免写死阈值
vol_pct = rolling_percentile(ann_vol_series, ann_vol, lookback=504)   # 2 年分布
dd_severe = (max_drawdown_1y <= -0.30)
if vol_pct is None:               risk_state = "unknown"
elif vol_pct >= 0.95 or dd_severe: risk_state = "high"
elif vol_pct >= 0.80:             risk_state = "elevated"
elif vol_pct >= 0.40:             risk_state = "moderate"
else:                             risk_state = "low"
```

### 21.8 数据要求

| 度量 | 最少 | 推荐 | 说明 |
|---|:---:|:---:|---|
| 回撤 / VaR / 风险调整 | 120 | 252 | < 120 → `risk_state="unknown"`，标 partial |
| risk_state 自校准 | 252 | 504 | 波动率分位需较长历史（2 年） |
| ATR 止损 | 15 | 30 | 复用 Layer 1 ATR |

### 21.9 constraint_exports（P3；四项风险度量已注册为 hard）

| export_ref | 说明 | registration_status | can_support_hard | allowed |
|---|---|:---:|:---:|:---:|
| `metric://max_drawdown_1y` | 近 1 年最大回撤 | `registered` | true | `["hard","soft"]` |
| `metric://hist_var_95_1y` | 历史 VaR(95%) | `registered` | true | `["hard","soft"]` |
| `metric://downside_deviation_ann` | 年化下行波动 | `registered` | true | `["hard","soft"]` |
| `metric://annualized_vol_1y` | 年化波动率 | `registered` | true | `["hard","soft"]` |
| `label://risk_state` | 风险状态标签 | `unregistered_mvp_local` | false | `["soft"]` |

> **已注册（§25.3）：** `max_drawdown_1y`、`hist_var_95_1y`、`downside_deviation_ann`、`annualized_vol_1y` 已注册为 `computed` 且 `can_support_hard_constraint = true`——它们是 Playbook 风险约束（如"近 1 年最大回撤不得超过 X""年化波动率上限"）最自然的载体（实现：`metrics_registry.py`）。

---

## 22. Feature D：支撑阻力与成交量分布（横切，P4）

### 22.1 概览

SPEC-004 §35.1 #7（支撑阻力）、#8（突破/跌破）是授权职责，但 Part I 在 §10.1 把 `key_levels` 强制置空。本特性真正实现 `support_resistance_metrics`（Evidence #12），并据此**解锁 `key_levels`**（契约更新见 §22.6 + §10.1）。

```text
点位来源（多源叠加，按成交量背书优先）:
  1. 成交量分布: POC / 价值区 VAH-VAL / 高低成交量节点 HVN-LVN   ← 主源（有成交量背书）
  2. 摆动枢轴聚类: 复用 Layer 2 find_peaks 的 swing highs/lows  ← 价格结构
  3. 均线汇聚: SMA50 / SMA200（复用 Layer 1）                   ← 动态点位
  4. 整数关口: 邻近的心理整数价                                 ← 辅助
合成: 聚类去重 → 打分 → 拆分为 support[]（价下）/ resistance[]（价上）
```

### 22.2 Evidence：support_resistance_metrics

```text
evidence_type: "support_resistance_metrics"     # SPEC-004 §36 #7 已注册类型
generation_type: computed
determinism_level: structured     # POC/VA 为 computed；点位聚类/打分含启发式
can_support_hard_constraint: false
数据来源: stock_daily (high, low, close, volume) + Layer 1 (SMA)

metrics:
  poc_price: float                  # Point of Control（成交量最大价位）
  value_area_high: float            # VAH（70% 成交量上沿）
  value_area_low: float             # VAL（70% 成交量下沿）
  price_vs_value_area: str          # "above" | "inside" | "below"
  nearest_support: float | None     # 价下最近的强支撑
  nearest_resistance: float | None  # 价上最近的强阻力
  support_levels: list[Level]       # 见下（已排序、去重、打分）
  resistance_levels: list[Level]
  hvn_prices: list[float]           # 高成交量节点（潜在支撑/阻力）
  lvn_prices: list[float]           # 低成交量节点（价格易快速穿越）

Level = {
  "price": float,
  "strength": float,    # 0.0–1.0
  "source": str,        # "volume_poc" | "volume_node" | "swing_pivot" | "ma" | "round"
  "touches": int,       # 触及次数（枢轴源）
}
```

### 22.3 成交量分布（Volume Profile）

```python
def volume_profile(high, low, close, volume, lookback=120, n_bins=24, va_pct=0.70):
    h, l, c, v = high[-lookback:], low[-lookback:], close[-lookback:], volume[-lookback:]
    lo, hi = float(np.min(l)), float(np.max(h))
    edges = np.linspace(lo, hi, n_bins + 1)
    vol_by_bin = np.zeros(n_bins)
    # 将每根 K 线的成交量按其 [low, high] 跨越的 bin 均摊（更准确）
    for i in range(lookback):
        b_lo = np.searchsorted(edges, l[i], side="right") - 1
        b_hi = np.searchsorted(edges, h[i], side="right") - 1
        b_lo, b_hi = max(b_lo, 0), min(b_hi, n_bins - 1)
        span = b_hi - b_lo + 1
        vol_by_bin[b_lo:b_hi + 1] += v[i] / span
    centers = (edges[:-1] + edges[1:]) / 2
    poc_idx = int(np.argmax(vol_by_bin))
    poc_price = float(centers[poc_idx])
    # 价值区：从 POC 向两侧扩展，每步并入相邻较大者，直到累计达 va_pct
    total = vol_by_bin.sum(); included = {poc_idx}; acc = vol_by_bin[poc_idx]
    lo_i = hi_i = poc_idx
    while acc < va_pct * total and (lo_i > 0 or hi_i < n_bins - 1):
        down = vol_by_bin[lo_i - 1] if lo_i > 0 else -1
        up   = vol_by_bin[hi_i + 1] if hi_i < n_bins - 1 else -1
        if up >= down: hi_i += 1; included.add(hi_i); acc += up
        else:          lo_i -= 1; included.add(lo_i); acc += down
    return dict(poc_price=poc_price,
                value_area_high=float(edges[hi_i + 1]),
                value_area_low=float(edges[lo_i]),
                vol_by_bin=vol_by_bin, centers=centers)
```

**HVN/LVN：** 对 `vol_by_bin` 做局部极值检测——局部峰为 HVN（潜在支撑/阻力），局部谷为 LVN（价格易快速穿越、不宜设点位）。

### 22.4 摆动枢轴聚类（复用 Layer 2）

```python
# 直接复用 §7.2 的 find_peaks 摆动检测，得到 swing highs/lows 的价位
swing_levels = price[swing_high_idx].tolist() + price[swing_low_idx].tolist()
# 聚类：价差 < max(1.5%, 0.5×ATR%) 的点位合并，touches = 簇内点数
clusters = cluster_by_proximity(swing_levels, tol=max(0.015, 0.5 * atr_pct_14d / 100))
```

### 22.5 点位合成与打分

```python
strength = clip(
    0.40 * volume_backing      # 成交量背书（POC=1.0, HVN 按相对高度, 其他 0）
  + 0.30 * touch_score         # 触及次数（枢轴源，touches 越多越强）
  + 0.20 * recency_score       # 近端触及加权
  + 0.10 * confluence_score,   # 多源重合（如枢轴 + 均线 + 整数同价位）
    0.0, 1.0)
```

合成后按价格排序、去重（邻近簇合并取最高 strength），以当前 close 拆分：`< close` 入 `support_levels`，`> close` 入 `resistance_levels`，各取 strength 最高的前若干个。

### 22.6 key_levels 输出（更新 §10.1 契约）

实现 D 后，§10.1 的"`key_levels.support/resistance` MUST be `[]`"约束**解除**，改为：

```json
"key_levels": {
  "support":    [{"price": 12.30, "strength": 0.72, "source": "volume_poc", "touches": 0}],
  "resistance": [{"price": 14.10, "strength": 0.65, "source": "swing_pivot", "touches": 3}],
  "source": "support_resistance_metrics",
  "poc": 13.05, "value_area": [12.50, 13.80]
}
```

> **契约迁移：** 仅当 `support_resistance_metrics` 实际计算成功时 `key_levels` 方可非空；D 未启用或数据不足时仍为 `[]`（保持向后兼容）。原契约测试 `test_key_levels_must_be_empty` 改为 `test_key_levels_empty_unless_sr_enabled`（§27）。

### 22.7 数据要求

| 度量 | 最少 | 推荐 | 说明 |
|---|:---:|:---:|---|
| 成交量分布 | 60 | 120 | bin 数据稀疏度 |
| 枢轴聚类 | 60 | 120 | 复用 §7.5 背离数据要求 |

### 22.8 constraint_exports（P4，soft-only）

| export_ref | 说明 | registration_status | can_support_hard | allowed |
|---|---|:---:|:---:|:---:|
| `metric://poc_price` | 成交量控制点 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://nearest_support` | 最近强支撑 | `unregistered_mvp_local` | false | `["soft"]` |
| `metric://nearest_resistance` | 最近强阻力 | `unregistered_mvp_local` | false | `["soft"]` |
| `label://price_vs_value_area` | 价格相对价值区 | `unregistered_mvp_local` | false | `["soft"]` |

> 点位含启发式聚类，`structured`、soft-only。`support_resistance_metrics` 虽为 SPEC-004 §36 已注册的 **Evidence 类型**，但其**具体 export_ref**仍需在 SPEC-005 注册后方可参与更强约束。

---

## 23. Feature F：多时间框架共振（横切，P4）

### 23.1 概览

只看日线极易被噪声与假突破误导。对中线投资者，**周线趋势是主导背景**——"顺着大周期方向做"。本特性把日线重采样为周线/月线，复用 Layer 1 指标计算各周期趋势，并打多周期对齐分。

### 23.2 Evidence：multi_timeframe_metrics

```text
evidence_type: "multi_timeframe_metrics"
generation_type: computed
determinism_level: computed     # 重采样 + TA-Lib，全确定性
can_support_hard_constraint: false
数据来源: stock_daily (OHLCV) 重采样

metrics:
  weekly_trend_state: str           # 复用 §6.2 Trend Classifier（周线输入）
  monthly_trend_state: str
  weekly_rsi_14: float
  weekly_macd_histogram: float
  weekly_price_above_30w_ma: bool   # 30 周均线 ≈ 日线 150 日（Stage Analysis 经典）
  mtf_alignment: str                # "aligned_bullish" | "aligned_bearish" | "conflicting" | "mixed"
  mtf_alignment_score: float        # −1.0（全空一致）… +1.0（全多一致）
```

### 23.3 重采样

```python
def resample_ohlcv(daily: pd.DataFrame, rule: str) -> pd.DataFrame:
    """rule='W-FRI'（周）或 'ME'（月）。使用前复权价（§5.3）。"""
    df = daily.set_index(pd.to_datetime(daily["trade_date"]))
    out = pd.DataFrame({
        "open":   df["open"].resample(rule).first(),
        "high":   df["high"].resample(rule).max(),
        "low":    df["low"].resample(rule).min(),
        "close":  df["close"].resample(rule).last(),
        "volume": df["volume"].resample(rule).sum(),
    }).dropna()
    return out
```

> **复权一致性：** 重采样前 **MUST** 已应用 §5.3 前复权；否则周/月线在除权周出现断层。

### 23.4 多周期对齐打分

```python
# 各周期趋势方向映射为分值（复用 §9.3 label_to_score 的 trend 部分）
dir_score = {"uptrend": +1, "downtrend": -1, "sideways": 0,
             "trend_reversal": 0, "unknown": 0}
d = dir_score[daily_trend_state]      # 来自 Part I §6.2
w = dir_score[weekly_trend_state]
m = dir_score[monthly_trend_state]
# 加权：大周期权重更高（月 0.5 / 周 0.3 / 日 0.2）
mtf_alignment_score = 0.5 * m + 0.3 * w + 0.2 * d

if   m > 0 and w > 0 and d > 0:  mtf_alignment = "aligned_bullish"
elif m < 0 and w < 0 and d < 0:  mtf_alignment = "aligned_bearish"
elif sign(m) != sign(d) and m != 0 and d != 0:  mtf_alignment = "conflicting"
else:                            mtf_alignment = "mixed"
```

> **用途：** `aligned_*` 提升对应方向 stance 的 confidence（§24.2）；`conflicting`（如日线涨、月线跌）触发 §24.3 一致性告警。

### 23.5 数据要求

| 周期 | 最少日线 | 推荐 | 说明 |
|---|:---:|:---:|---|
| 周线指标 | 250（≈50 周） | 350 | 周线 SMA/MACD warmup |
| 月线趋势 | 500（≈24 月） | 750 | 月线样本稀疏，趋势粗判 |

> 数据不足以构造月线时，`monthly_trend_state = "unknown"`，对齐打分退化为日/周两级。

### 23.6 constraint_exports（P4，soft-only）

| export_ref | 说明 | registration_status | can_support_hard | allowed |
|---|---|:---:|:---:|:---:|
| `metric://mtf_alignment_score` | 多周期对齐分 | `unregistered_mvp_local` | false | `["soft"]` |
| `label://weekly_trend_state` | 周线趋势 | `unregistered_mvp_local` | false | `["soft"]` |
| `fact://mtf_aligned_bullish` | 多周期共振看多 | `unregistered_mvp_local` | false | `["soft"]` |

---

## 24. 集成更新：Pipeline / Stance / Confidence

### 24.1 Pipeline 扩展（在 §9.1 九步管线基础上）

Part II 的计算插入在 Step 2（Layer 1）之后、Step 5（分类）之前，**不改变** §9.1 既有步骤编号：

```text
Step 2  Layer 1 基础指标（Part I）
Step 2A [P3] §18 自校准基线 + Feature A 市场状态（Layer 0）
Step 2B [P3] Feature C 风险度量
Step 2C [P3] Feature B 相对强度（需基准数据，§26；P3 前置条件）
Step 2D [P4] Feature D 支撑阻力 + Feature F 多时间框架
Step 3  Layer 2 背离（Part I）
Step 4  Layer 3 威科夫（Part I）
Step 5  分类（Part I §6 + Part II 各 *_state）
Step 6  Stance（§9.3 + §24.2 regime 门控 + §24.3 调整因子）
Step 7  Confidence（§9.4 + §24.4）
Step 8–9 Card 组装 / 验证（§9.5 + §12 + §24.5 新增检查）
```

各 Feature 段独立 try/except：任一高阶 Feature 计算失败 → 该段 Evidence 标缺失（`_OPTIONAL_EVIDENCE`），记 `warnings`，**不**使整域失败。

### 24.2 regime 门控（Feature A 调制下游）

> **P3+ 管线插入点（关闭审查 P0 #1）：** Part II 启用后，§9.3 算出 `raw_score`（含 Layer 1 加权 + 背离/威科夫调整）后，**先**应用本节 regime 门控与 §24.3 Part II 调整因子，**再**执行 clip 与 Phase 3 stance 映射。§9.3 代码块中的 clip + stance 判定在 P3+ **延迟**至 §24.2.1 全部步骤完成后执行；P0–P2 无 regime，按 §9.3 原流程立即 clip 并映射。

market regime 作为**统一调制器**缩放下游信号，而非简单线性相加。在 §9.3 算出 `raw_score` 后、**P3+ clip 之前**应用：

```python
# 1) 机制对"信号类型"的适配（trending 利好趋势信号；mean_reverting 利好反转信号）
if regime == "trending":
    # 趋势/动量为主，背离反转信号降权（强趋势中背离常失败）
    if divergence_assessment.get("has_regular_bearish") and labels.get("trend") == "uptrend":
        raw_score += 0.05    # 弱化（原 §9.3 为 −0.15，此处部分回补）
elif regime == "mean_reverting":
    # 反转信号增权
    if divergence_assessment.get("has_regular_bullish"):
        raw_score += 0.10
    if divergence_assessment.get("has_regular_bearish"):
        raw_score -= 0.10
    if labels.get("trend") == "downtrend" and divergence_assessment.get("has_regular_bullish"):
        raw_score += 0.05    # 对称：下跌趋势中的底背离部分回补

# 2) 机制对 confidence 的调制（random 环境无边际，降信心）
regime_conf_mult = {
    "trending": 1.00, "mean_reverting": 1.00,
    "random": 0.85, "unknown": 0.90,
}[regime]
```

> **设计立场（横切原则）：** 这是"regime 门控范式"的落地——让市场状态调制其他信号的权重与置信度，而不是把它们平均成一个黑箱分数（对齐 SPEC-001 §6 "系统应暴露冲突，而不是把冲突平均成黑箱分数"）。门控权重本身未经回测，列为 §28 开放项，并在 `domain_payload.threshold_calibration` 标注。

#### 24.2.1 P3+ clip / stance 延迟执行与 signal_conflict 合成

> **Step 6 作用域说明：** 本节与 §9.3、§24.2、§24.3 同属 **Step 6（Stance Determination）** 的同一实现单元（如 `_determine_stance(...)`）。§9.3 Phase 2 计算的 `layer1_conflict`、`divergence_trend_conflict_raw` 等为**函数内局部变量**，不跨 Step 7+ 持久化；§24.2.1 在同一函数内、clip 之前消费并重算 `signal_conflict`。

**P3+ 完整 Step 6 顺序：**

```text
1. §9.3  raw_score（Layer 1 + 背离/威科夫；不 clip）
2. §24.2 regime 门控调整 raw_score；记录 regime_conf_mult
3. §24.3 Part II 调整因子（RS / MTF / 风险）
4. score = clamp(raw_score, −1.0, 1.0)
5. signal_conflict 合成（含 regime 感知，见下）
6. Phase 3 stance 映射（§9.3 边界值表）
```

**regime 对 signal_conflict 的调制（关闭审查 P0 #2）：**

trending regime 下 regular 背离与趋势的标签矛盾已被 §24.2 门控削弱（"强趋势中背离常失败"）。若 `divergence_trend_conflict` 仍计入 `signal_conflict`，在 `|score| ≤ 0.5` 时会产出 `mixed`，与 regime 意图矛盾——regime 想说"趋势中的背离别太当真"，但 `mixed` 反而放大了冲突。

```python
# 复用 §9.3 Phase 2 的 layer1_conflict 与 divergence_trend_conflict_raw
# divergence_trend_conflict_raw 已在 §9.3 计算

if regime == "trending":
    # trending 下背离-趋势对不算显式冲突（regime 已降权背离意义）
    divergence_trend_conflict = False
else:
    divergence_trend_conflict = divergence_trend_conflict_raw

signal_conflict = layer1_conflict or divergence_trend_conflict
# 接 §9.3 Phase 3 stance 映射（使用步骤 4 的 score）
```

> P0–P2 无 `regime_metrics`，`divergence_trend_conflict` 与 `signal_conflict` 按 §9.3 原逻辑，不受本节影响。`layer1_conflict` 不受 regime 调制——多维分类器方向冲突在任何 regime 下均为显式矛盾。

### 24.3 stance 调整因子增补（扩展 §9.3）

在 §9.3 既有调整后追加（裁剪到 [−1,1] 之前）：

```python
# 相对强度（Feature B）
if rs_state == "leader":   raw_score += 0.10
if rs_state == "laggard":  raw_score -= 0.10
# 多周期共振（Feature F）
raw_score += 0.10 * mtf_alignment_score      # −0.1 … +0.1
# 风险（Feature C）：极端风险压低多头立场（风险厌恶）
if risk_state == "high":   raw_score -= 0.10
```

#### 调整因子总预算与累加风险（审查 P2 #8）

Part I（§9.3）与 Part II（§24.2–§24.3）在 **clip 之前**对同一 `raw_score` 线性叠加。各段单项上界如下：

| 来源 | 触发条件 | 单项范围 | 理论最大 |
|---|---|---|:---:|
| §9.3 背离 | regular bullish / bearish | ±0.15 | ±0.15 |
| §9.3 威科夫 | accumulation/distribution C/D | ±0.20 | ±0.20 |
| §24.2 regime 门控 | trending / mean_reverting 适配 | ±0.10 | ±0.10 |
| §24.3 RS | `leader` / `laggard` | ±0.10 | ±0.10 |
| §24.3 MTF | `mtf_alignment_score` | ±0.10 | ±0.10 |
| §24.3 风险 | `risk_state=high` | −0.10 | −0.10 |

**累加风险：** 上表独立触发时，clip 前理论叠加最大约 **±0.65**，可能使 Layer 1 加权方向（`layer1_only_score = Σ weights × label_to_score`）被后续调整因子**完全覆盖甚至翻转**。这与"Layer 1 定方向、Layer 2/3 微调"的设计直觉存在张力，但当前 MVP **有意保留**该灵活性——regime / RS / 风险等横切维度在特定场景下应能压过单一 Layer 1 读数。

**设计约束（MVP）：**

1. **clip 保底：** `score = clamp(raw_score, −1.0, 1.0)` 保证 stance 映射输入合法；不因累加越界。
2. **翻转告警：** 实现时 **SHOULD** 在 clip 前检测调整因子是否单独翻转方向——若 `sign(raw_score) ≠ sign(layer1_only_score)` 且 `|layer1_only_score| > 0.2`，则 `warnings.append("adjustment_override: Part II 调整因子翻转 Layer 1 方向")`。该告警不阻断 Card 产出，但进入 Decision Trace 供 Playbook / 人工复核消费。
3. **无硬顶预算：** MVP **不**对 Part II 调整因子设全局 `±cap`（如 ±0.25）——各系数未经回测，硬顶可能引入新的边界伪影。总预算与各系数校准列为 **§28.1 开放项**；回测后可在 `threshold_calibration.part_ii` 旁增配 `adjustment_budget` 元数据。

> **应用顺序依赖：** §24.2 regime 门控先于 §24.3 Part II 因子执行（§24.2.1 步骤 2→3）。同一事件（如 trending + bearish divergence）在 regime 与 §9.3 背离调整中均有响应——regime 部分回补后，§24.3 不再重复处理该路径。

### 24.4 confidence 增补（扩展 §9.4）

```python
# 在 §9.4 三因子 confidence 基础上：
confidence *= regime_conf_mult               # §24.2

# 多周期一致/冲突
if mtf_alignment in ("aligned_bullish", "aligned_bearish"):
    confidence *= 1.10
elif mtf_alignment == "conflicting":
    confidence *= 0.90

# 乘性调整后再次应用 SPEC-004 绝对上限（data_quality / domain_status）
confidence = min(confidence, spec004_card_cap)

# 波动率极端 / 高风险压上限（与 §12.3 风格一致）
if volatility_regime == "extreme" or risk_state == "high":
    confidence = min(confidence, 0.60)
# 最终仍受 SPEC-004 §7.3 data_quality / domain_status 上限约束（由模型校验器强制）
```

### 24.5 域级验证增补（扩展 §12.1，新增 #9–#13）

| # | 检查项 | 级别 | 处理 |
|:---:|---|:---:|---|
| 9 | `regime=random` 但 stance 为强方向（\|score\|>0.5） | note | `warnings.append("low_edge_regime: 随机游走环境，方向性判断边际有限")` |
| 10 | `mtf_alignment=conflicting`（日线与月线方向相反） | note | 记录，不阻断（正常的周期错位） |
| 11 | `risk_state=high` 但 `stance ∈ {positive, moderately_positive}` | flag | `confidence = min(confidence, 0.55)`，`warnings.append("high_risk_positive_stance")` |
| 12 | `rs_state=laggard` 但 `stance` 正面 | note | `warnings.append("relative_weakness_vs_benchmark")` |
| 13 | Feature B 启用但 `benchmark_unavailable` | note | relative_strength_metrics 缺失计入 evidence_coverage |

---

## 25. constraint_exports 增补（Part II 汇总）

> 总则见 §11.0 / §17.3。下列默认 `registration_status = "unregistered_mvp_local"`、`can_support_hard_constraint = false`、`allowed_constraint_types = ["soft"]`（受 SPEC-004 §9.1 校验器强制）。
>
> **例外（已注册，§25.3）**：下列 6 项已升级为 `registration_status = "registered"`、`can_support_hard_constraint = true`、`allowed_constraint_types = ["hard", "soft"]`——`max_drawdown_1y`、`hist_var_95_1y`、`downside_deviation_ann`、`annualized_vol_1y`、`beta_252d`、`relative_drawdown`。实现落点：`crosslens_technical_market.metrics_registry`（`MetricRegistryEntry` 数据）+ `card.py::_build_risk_exports` / `_build_relative_strength_exports`；契约测试 `tests/test_metrics_registry.py`。

### 25.1 P3（§18 自校准 + A 市场状态 + B 相对强度 + C 风险）

汇总 §19.8 + §20.9 + §21.9：

- **A**：`metric://hurst_exponent`、`metric://efficiency_ratio`、`label://market_regime`、`fact://regime_is_trending`
- **B**：`metric://rs_raw`、`metric://beta_252d`、`metric://relative_drawdown`、`label://rs_state`
- **C**：`metric://max_drawdown_1y`、`metric://hist_var_95_1y`、`metric://downside_deviation_ann`、`metric://annualized_vol_1y`、`label://risk_state`

### 25.2 P4（D 支撑阻力 + F 多时间框架）

汇总 §22.8 + §23.6：`metric://poc_price`、`metric://nearest_support`、`metric://nearest_resistance`、`label://price_vs_value_area`、`metric://mtf_alignment_score`、`label://weekly_trend_state`、`fact://mtf_aligned_bullish`。

### 25.3 SPEC-005 注册请求清单（升级为 registered 的候选）

> **状态（已落地）：** 标 ✅ 的 6 项已完成注册并实现，落点见 §25 例外说明；`hurst_exponent` / `efficiency_ratio` / `rs_raw` 经评估维持 soft（理由见末列），`risk_state` / `rs_state` 等结构化标签维持 soft。

向 SPEC-005 提交以下 `MetricRegistryEntry`；注册后 `registration_status → registered`，标 ✅ 者拟 `can_support_hard_constraint = true`：

| metric_id | metric_category | 注册后可 hard | 用途（Playbook 约束示例） |
|---|:---:|:---:|---|
| `max_drawdown_1y` | computed | ✅（已注册） | "近 1 年最大回撤不得超过 35%" |
| `hist_var_95_1y` | computed | ✅（已注册） | "日 VaR(95%) 不得劣于 −8%" |
| `downside_deviation_ann` | computed | ✅（已注册） | 下行波动上限 |
| `annualized_vol_1y` | computed | ✅（已注册） | 年化波动率上限 |
| `beta_252d` | computed | ✅（已注册） | "组合/标的 Beta 上限" |
| `relative_drawdown` | computed | ✅（已注册） | 相对基准回撤上限 |
| `hurst_exponent` | computed | ❌（维持 soft） | regime 上下文，soft 规则引用 |
| `efficiency_ratio` | computed | ❌（维持 soft） | 趋势质量，soft |
| `rs_raw` | computed | ❌（维持 soft） | 相对强度评分（IBD 风格 ROC 加权）；横截面排名依赖全市场快照（§28.3），不宜单独用作 hard 准入依据 |

> 其余 `structured` 标签（regime、risk_state、rs_state、price_vs_value_area、weekly_trend_state）建议长期保持 soft（含启发式，不宜单独构成硬性准入/禁入）。

---

## 26. 数据契约变更（Feature B，P3 前置条件）

### 26.1 Adapter 新增方法

```python
def get_index_data(index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """基准指数日线。返回列: trade_date, close（升序）。
    AlphaDB 落点: rawdata.index_daily（Tushare index_daily）。"""
```

| StandardContract 列 | AlphaDB 原始列 | 说明 |
|---|---|---|
| `trade_date` | `trade_date` | 交易日 YYYYMMDD |
| `close` | `close` | 指数收盘点位 |

### 26.2 行业基准映射（可选增强）

行业相对强度需"个股 → 申万一级行业指数"映射。`get_industry_peers`（已存在）返回同业 ts_code；行业指数代码可由行业分类映射表解析（如申万一级行业指数 `801xxx.SI`）。MVP 可先只用市场基准（沪深300），行业基准列为增强项。

### 26.3 降级路径

| 缺失 | 行为 |
|---|---|
| `index_daily` 不可用 | `relative_strength_metrics` 整段不产出；`warnings.append("benchmark_unavailable")`；不影响 domain_status（B 为 optional） |
| 个股/基准交易日不齐 | 取交集日期；交集 < 120 日 → Beta/Alpha 置 `None` |

> **MockAdapter / TinyData：** 需补 `get_index_data` 的桩实现（返回合成指数序列），保证 P3 单测不依赖真实数据源（对齐 §5.1 "MockAdapter 测试不依赖 TA-Lib" 风格）。

---

## 27. 测试策略增补

### 27.1 包结构增补（扩展 §13.1）

```text
src/crosslens_technical_market/
  regime/            # Feature A
    __init__.py
    hurst.py         # R/S 估计
    efficiency.py    # Kaufman ER
    classifier.py    # regime 合成
  relative_strength/ # Feature B
    __init__.py
    rs.py            # RS 线 / RS Rating / Mansfield
    beta.py          # Beta / Alpha
  risk/              # Feature C
    __init__.py
    drawdown.py      # 回撤分析
    downside.py      # VaR / CVaR / 下行波动
    ratios.py        # Sharpe/Sortino/Calmar + ATR 止损
  levels/            # Feature D
    __init__.py
    volume_profile.py
    pivots.py        # 复用 divergence.detector 的 find_peaks
    builder.py       # 点位合成打分
  multi_timeframe/   # Feature F
    __init__.py
    resample.py
    confluence.py
  calibration.py     # §18 分位自校准（横切工具）
```

### 27.2 测试分层（扩展 §13.2）

| 层级 | 阶段 | 测试文件 | 覆盖 |
|---|:---:|---|---|
| 自校准 | P3 | `tests/test_calibration.py` | rolling_percentile + bucket + 样本不足 None |
| 市场状态 | P3 | `tests/test_regime.py` | Hurst（趋势/均值回归/随机合成序列）+ ER + regime 合成 |
| 风险度量 | P3 | `tests/test_risk.py` | 回撤 / VaR / CVaR / Sortino / Calmar / ATR 止损 / risk_state |
| 支撑阻力 | P4 | `tests/test_levels.py` | 成交量分布 POC/VA/HVN/LVN + 枢轴聚类 + key_levels 输出 |
| 多周期 | P4 | `tests/test_mtf.py` | 重采样正确性 + 对齐打分 + 月线不足降级 |
| 相对强度 | P3 | `tests/test_relative_strength.py` | RS Rating / Beta / Mansfield / 基准缺失降级 |
| 集成 | P3+ | `tests/test_technical_pipeline.py`（扩展） | regime 门控 + stance/confidence 调整 |

### 27.3 关键测试用例

```text
# 自校准
test_percentile_basic / test_percentile_insufficient_returns_none

# Feature A
test_hurst_trending_series (合成 H>0.55) / test_hurst_mean_reverting (H<0.45)
test_efficiency_ratio_clean_trend_high / test_regime_random_lowers_confidence

# Feature C
test_max_drawdown / test_var_historical_fat_tail / test_sortino / test_calmar
test_risk_state_high_caps_confidence (集成 §24.4)
test_atr_stop_long

# Feature D
test_volume_profile_poc / test_value_area_70pct / test_hvn_lvn
test_levels_split_support_resistance_by_close
test_key_levels_empty_unless_sr_enabled   # 替换 §13.6 的 test_key_levels_must_be_empty

# Feature F
test_resample_weekly_ohlc / test_mtf_aligned_bullish / test_mtf_conflicting_note

# Feature B
test_rs_rating_weighted_roc / test_beta_ols / test_mansfield_zero_cross
test_benchmark_unavailable_degrades

# 集成
test_regime_gating_trending_discounts_bearish_divergence
test_high_risk_positive_stance_flag (验证 #11)
```

### 27.4 契约测试更新

> §13.6 的 `test_key_levels_must_be_empty` 在 P4 后**失效**——改为 `test_key_levels_empty_unless_sr_enabled`：未启用 D 或数据不足时 `key_levels.support/resistance == []`；启用且计算成功时允许非空且每个 Level 结构合法。其余 P0 契约测试（registered-only hard exports 等）保持不变——Part II 全部为 soft export，不违反 P0 的"仅 7 个 registered hard exports"约束。

---

## 28. 开放问题增补（扩展 §14）

| # | 开放问题 | 说明 / 建议路径 |
|:---:|---|---|
| 28.1 | regime 门控权重未校准 | §24.2/§24.4 的调制系数（0.85/1.10/0.10 等）为经验值，需回测；`threshold_calibration` 标注 |
| 28.2 | Hurst 估计稳定性 | R/S 法短窗方差大；可评估 DFA（去趋势波动分析）或 wavelet 估计作为替代/交叉验证 |
| 28.3 | 横截面 RS Rating | 真正的 IBD 1–99 需全市场快照；依赖批量/选股上下文（SPEC-001 §12.2 多股票扫描），MVP 用自校准近似 |
| 28.4 | 参数化波动率预测 | §21.4 用历史法；后续可评估 GARCH / Markov-switching GARCH 提升左尾与前瞻性（调研支持 regime-aware 占优） |
| 28.5 | Part I 分类器迁移自校准 | §6 的固定阈值（RSI 70/30、ATR% 等）可逐步迁移到 §18 自校准，统一校准口径 |
| 28.6 | 行业相对强度 | §26.2 行业指数映射未在 MVP 落地；需申万行业指数代码映射表 |

---

*End of SPEC-014 v0.2.3*
