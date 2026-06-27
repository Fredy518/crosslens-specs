# SPEC-013：Fundamentals 域实现规格

**版本：** v0.2.0
**状态：** Review
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.7；SPEC-005 v0.2
**上游契约：**
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-003 §6.5 (Evidence Packet schema)
- SPEC-004 §17~§22 (Fundamentals 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-004 §4 (Analysis Card 通用 Schema)
- SPEC-004 §45 (MVP 最小实现范围)
- SPEC-005 §5 (Metric Registry)
- SPEC-005 §4.4 (Evidence Packet confidence 取值规则)
**目标阶段：** 域实现规格 / MVP 实现前置

---

## 1. 文档目标

本 SPEC 定义 Fundamentals 能力域**内部如何工作**——从 Context Bundle + Evidence Packets 到 Analysis Card 的完整管线。

- SPEC-004 §17~§22 定义了 Fundamentals 的"做什么"（WHAT），本 SPEC 定义"怎么做"（HOW）
- 本 SPEC 不修改上游契约。如果实现过程中发现上游契约有缺口，应记录在 §12 开放问题中，由后续修订向上游 SPEC 提变更请求
- 本 SPEC 的确定性部分（computed metrics、structured classifiers、confidence aggregation）应全部可单元测试

---

## 2. 域目标与边界

Fundamentals 能力域负责分析公司的基本面质量、财务表现、估值状态和长期投资基础。

**Fundamentals 负责：**
1. 收入增长分析（增速、驱动因素、持续性）
2. 盈利能力评估（毛利率、经营利润率、ROE/ROIC）
3. 现金流质量（自由现金流、现金流转换率、资本开支效率）
4. 资产负债表健康度（杠杆、流动性、债务结构）
5. 估值水平（绝对估值、相对估值、历史分位）
6. 同业比较（行业对标、竞争力位置）
7. 资本配置质量（再投资、回购、并购效率）
8. 盈利质量（应计项目、一次性项目、收入确认）

**Fundamentals 不负责：**
1. 短线交易择时 → Technical/Market 域
2. 社交媒体情绪 → Sentiment 域
3. 技术形态分析 → Technical/Market 域
4. 宏观预测 → Macro/Meso 域
5. 事件冲击路径的完整解释 → Event Driven 域
6. 最终买卖决策 → Playbook + Decision Candidate 层

**与其他域的切分边界：**

| 边界 | 归属 | 说明 |
|------|:----:|------|
| 收入增速 vs 宏观周期归因 | Fundamentals 提供数据，Macro 提供归因 | 两者独立 |
| 估值水平 vs 市场情绪 | Fundamentals | 估值是基本面域产出 |
| 财报发布事件 vs 财报数据 | Event Driven 管事件，Fundamentals 管数据 | 正交 |
| ROE 杜邦分解 | Fundamentals | 确定性计算 |

> **A 股适配：** MVP 阶段 Fundamentals 域仅支持 A 股上市公司（中国会计准则 CAS）。股票代码使用 `ts_code` 格式（如 `000001.SZ`、`600519.SH`），行业分类使用申万行业分类（SWHY）。多市场适配（港股、美股）不在 MVP 范围内。
>
> **A 股默认口径：** 财报可见性必须同时区分 `end_date`（报告期）、`ann_date`（公告日/披露日）与实际 `as_of` 可见日，不得仅按自然季度末推断数据可见性；财报新鲜度、TTM 拼接、历史回看窗口与 PIT 去重必须以 A 股披露节奏和 A 股交易日历为准，不得默认套用美股披露节奏或自然日近似。

---

## 3. Evidence Consumption & Derived Computation Catalog

Fundamentals 域消费 9 种 Evidence Packet 类型（由 Context & Evidence Layer 生产），全部继承自 SPEC-004 §18。域内部可以派生计算值（computed metrics / structured labels），但**不创建一级 Evidence Packet 回流到共享池**——除非编排器显式发出 evidence request 且域作为 evidence producer 角色响应。

> **架构边界（P0）：** Fundamentals Domain Runtime 的角色是 **消费者**，不是生产者。Evidence Packet 的生产属于 Context & Evidence Layer（SPEC-003 Layer 3）。如果域内部计算结果需要被其他域消费，应向编排器提出 evidence request，由编排器协调写入共享 Evidence Pool。

### 3.1 消费的 Evidence Packet 类型

| # | evidence_type | generation_type | determinism_level | can_support_hard | 来源 § |
|---|---|---|---|---|---|
| 1 | `financial_metrics` | computed | computed | true | SPEC-004 §18.1 |
| 2 | `growth_metrics` | computed | computed | true | SPEC-004 §18 |
| 3 | `margin_metrics` | computed | computed | true | SPEC-004 §18 |
| 4 | `cashflow_metrics` | computed | computed | true | SPEC-004 §18 |
| 5 | `balance_sheet_metrics` | computed | computed | true | SPEC-004 §18 |
| 6 | `valuation_metrics` | computed | computed | true | SPEC-004 §18.2 |
| 7 | `peer_comparison_metrics` | computed | computed | true | SPEC-004 §18 |
| 8 | `capital_allocation_metrics` | computed | computed | true | SPEC-004 §18 |
| 9 | `earnings_quality_metrics` | structured | structured | false | SPEC-004 §18 |

### 3.2 每种 Evidence Packet 的完整定义

#### 3.2.1 financial_metrics

```
evidence_type: "financial_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（income_statement, balance_sheet）
获取频率: 季度（A 股报告周期：Q1 3/31, Q2 6/30, Q3 9/30, Q4 12/31）
数据源映射:
  AlphaDB 利润表: rawdata.fina_income (字段: operating_revenue, operating_cost, net_profit_parent, ...)
  AlphaDB 资产负债表: rawdata.fina_balancesheet (字段: total_assets, total_equity, total_debt, ...)
  tinydata: td.fina_income() + td.fina_balancesheet()
  A 股财务报告周期: Q1(3/31) + Q2(6/30) + Q3(9/30) + Q4(12/31)
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `revenue_growth_ttm` | float | ratio | TTM 收入同比增长率 |
| `gross_margin_ttm` | float | ratio | TTM 毛利率 |
| `gross_margin_qoq_change` | float | ratio | 毛利率环比变动 |
| `operating_margin_ttm` | float | ratio | TTM 经营利润率 |
| `fcf_margin_ttm` | float | ratio | TTM 自由现金流率 |
| `net_debt_to_ebitda` | float | ratio | 净负债 / EBITDA |
| `roe_ttm` | float | ratio | TTM ROE |
| `roic_ttm` | float | ratio | TTM ROIC |
| `growth_capex_flag` | bool | — | 增长型资本开支标志 |

> **A 股字段映射：** `revenue_growth_ttm` 由 `fina_income.operating_revenue`（营业收入）计算；`gross_margin_ttm` 由 `operating_revenue - operating_cost` 或直接用 `fina_indicator.grossprofit_margin`；`roe_ttm` 使用 `fina_indicator.roe_dt`（归母扣非加权 ROE）；`roic_ttm` 需手动计算（参考 §4 metric://roic_ttm）。

**facts 字段：** 无（financial_metrics 纯 computed，不产 facts）

**labels 字段：** 无

**confidence 赋值规则：**
- 默认 1.0（computed evidence，SPEC-005 §4.4.1）
- 降级条件：财报数据距今天数 > 90 天 → confidence *= 0.85
- 降级条件：财报数据距今天数 > 180 天 → confidence *= 0.70
- 降级条件：数据源标记为 restated（重述） → confidence *= 0.90

**data_quality 判断：**
- 财报数据 ≤ 90 天 + 无 restated → high
- 财报数据 ≤ 180 天 → medium
- 财报数据 > 180 天 → low
- 数据源不可用 → unavailable

#### 3.2.2 growth_metrics

```
evidence_type: "growth_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（income_statement: AlphaDB `rawdata.fina_income` + tinydata `td.fina_income()`），需 ≥8 个季度历史
获取频率: 季度（A 股报告周期：Q1 3/31, Q2 6/30, Q3 9/30, Q4 12/31）
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `revenue_growth_ttm` | float | ratio | TTM 收入增速 |
| `revenue_growth_3y_cagr` | float | ratio | 3 年收入 CAGR |
| `revenue_growth_qoq` | float | ratio | 季度环比增速 |
| `earnings_growth_ttm` | float | ratio | TTM 盈利增速 |
| `earnings_growth_3y_cagr` | float | ratio | 3 年盈利 CAGR |
| `revenue_growth_consistency` | float | ratio | 过去 8 季度正增长的季度占比 |

**confidence 赋值规则：** 默认 1.0。历史数据不足 8 季度 → confidence *= 0.80。

#### 3.2.3 margin_metrics

```
evidence_type: "margin_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（income_statement）
获取频率: 季度（A 股报告周期：Q1 3/31, Q2 6/30, Q3 9/30, Q4 12/31）
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `gross_margin_ttm` | float | ratio | TTM 毛利率 |
| `gross_margin_qoq_change` | float | ratio | 毛利率 QoQ 变动（当前季度毛利率 - 前季度毛利率） |
| `operating_margin_ttm` | float | ratio | TTM 经营利润率 |
| `operating_margin_3y_avg` | float | ratio | 3 年经营利润率均值 |
| `net_margin_ttm` | float | ratio | TTM 净利率 |
| `margin_trend` | float | ratio | 过去 4 季度毛利率趋势斜率（线性回归 β） |

**公式示例：**
```
margin_trend = linear_regression_slope(
    x = [t-4, t-3, t-2, t-1],
    y = [gross_margin_q[t-4], ..., gross_margin_q[t-1]]
)
```

**confidence 赋值规则：** 默认 1.0。

#### 3.2.4 cashflow_metrics

```
evidence_type: "cashflow_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（cash_flow_statement）
获取频率: 季度（A 股报告周期：Q1 3/31, Q2 6/30, Q3 9/30, Q4 12/31）
数据源映射:
  AlphaDB 现金流量表: rawdata.fina_cashflow (字段: n_cashflow_act=经营活动现金流净额, c_cap_ex=资本开支)
  tinydata: td.fina_cashflow()
  A 股现金流量表字段名不同于美股: "经营活动产生的现金流量净额" → n_cashflow_act; "购建固定资产、无形资产和其他长期资产支付的现金" → c_cap_ex
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `fcf_margin_ttm` | float | ratio | TTM FCF / Revenue |
| `fcf_conversion_rate` | float | ratio | FCF / Net Income（TTM） |
| `operating_cashflow_ttm` | float | currency | TTM 经营性现金流 |
| `capex_to_revenue_ttm` | float | ratio | CapEx / Revenue（TTM） |
| `fcf_stability` | float | ratio | 过去 4 年正 FCF 年数占比 |
| `fcf_ttm` | float | currency | TTM 自由现金流（internal：用于派生 fcf_yield，见 §4.2） |

> **NOTE：** `fcf_yield` 不在 consumed Evidence Packet 中。它是 Fundamentals runtime 内部派生的 derived metric（FCF_ttm / market_cap），只出现在 constraint_exports 中，不回流到 Evidence Pool。详见 §4.2。

> **A 股字段映射：** `fcf_ttm = sum(n_cashflow_act[c_t-3..c_t]) - sum(c_cap_ex[c_t-3..c_t])`（其中 n_cashflow_act 为经营活动现金流净额，c_cap_ex 为资本开支现金流出）。A 股 CAS 的 CapEx 编码为 `c_cap_ex` 而非常见的 `capex`。

**facts 字段：**
| fact | 类型 | 说明 |
|------|------|------|
| `fcf_positive_ttm` | bool | TTM FCF > 0 |

**confidence 赋值规则：** 默认 1.0。

#### 3.2.5 balance_sheet_metrics

```
evidence_type: "balance_sheet_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（balance_sheet）
获取频率: 季度（A 股报告周期：Q1 3/31, Q2 6/30, Q3 9/30, Q4 12/31）
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `net_debt_to_ebitda` | float | ratio | 净负债 / EBITDA |
| `current_ratio` | float | ratio | 流动比率 |
| `debt_to_equity` | float | ratio | 负债权益比 |
| `interest_coverage` | float | ratio | EBIT / 利息支出 |
| `tangible_book_value_per_share` | float | currency | 每股有形账面价值 |
| `goodwill_to_assets` | float | ratio | 商誉 / 总资产 |

**confidence 赋值规则：** 默认 1.0。金融机构（银行/保险/券商，如 000001.SZ 平安银行）使用替代指标集 → balance_sheet_metrics 标记为 `data_quality=medium`（杠杆指标不适用于金融股）。

#### 3.2.6 valuation_metrics

```
evidence_type: "valuation_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 行情 API（price, market_cap, shares_outstanding） + 财务报表 API + 历史估值序列 DB
获取频率: 日（行情）+ 季度（财务）
数据源映射:
  AlphaDB 估值: rawdata.stock_dailybasic (字段: pe_ttm, pe, pb, total_mv=总市值(万元), circ_mv=流通市值(万元))
  AlphaDB 行情: rawdata.stock_daily (OHLCV + 复权因子)
  tinydata 行情: td.stock_daily() → OHLCV
  tinydata 估值: 需从 td.stock_daily() OHLCV 组合计算 PE/PB/市值
  5 年历史序列: AlphaDB stock_dailybasic 日线（~1250 交易日），按 PIT 需排除停牌日
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `pe_percentile_5y` | float | ratio | 当前 PE 在 5 年序列中的百分位 |
| `ev_ebitda_percentile_5y` | float | ratio | 当前 EV/EBITDA 在 5 年序列中的百分位 |
| `pe_current` | float | ratio | 当前 PE（TTM） |
| `ev_ebitda_current` | float | ratio | 当前 EV/EBITDA |
| `price_to_book` | float | ratio | P/B |
| `dividend_yield` | float | ratio | 股息率 |

> **NOTE：** `fcf_yield` 不在 consumed Evidence Packet 中。它是 derived metric——FCF 来自 cashflow_metrics.`fcf_ttm`，市值来自 market_data.`market_cap`。定义和导出规则见 §4.2。

> **A 股字段映射：** `pe_current` = `stock_dailybasic.pe_ttm`（每日 PE-TTM，总市值/归母净利润 TTM）；`pe_percentile_5y` 从 stock_dailybasic 5 年 PE 序列计算百分位。A 股 PE 计算使用归母净利润而非合并净利润。停牌期间的 PE 值应在百分位计算前剔除（否则会扭曲分位）。

**公式：**
```
pe_current = market_cap / net_income_ttm
pe_percentile_5y = percentile(pe_current, historical_pe_sequence_5y)
    where percentile(x, seq) = count(v <= x for v in seq) / len(seq)
fcf_yield = fcf_ttm / market_cap
```

**facts 字段：**
| fact | 类型 | 说明 |
|------|------|------|
| `pe_below_5y_median` | bool | PE < 5 年中位数 |

**confidence 赋值规则：**
- 默认 1.0
- 历史估值序列不足 3 年 → confidence *= 0.75
- 负盈利（PE 无意义）→ pe_percentile_5y = null, confidence *= 0.70
- 估值数据 > 5 个交易日未更新 → confidence *= 0.90

#### 3.2.7 peer_comparison_metrics

```
evidence_type: "peer_comparison_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 行业对标 DB（自建或商业）
获取频率: 季度
数据源映射:
  AlphaDB 行业分类: rawdata.stock_industry_versioned (申万 SWHY 为主)
  AlphaDB 行业成分: rawdata.index_swmember → 同行业 ts_code 列表
  AlphaDB 行业估值: 需 SQL 聚合同行业 stock_dailybasic（median PE/PB/ROE）
  tinydata 行业分类: td.stock_industry_versioned()
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `industry_median_revenue_growth_ttm` | float | ratio | 行业中位数 TTM 收入增速 |
| `industry_median_pe` | float | ratio | 行业中位数 PE |
| `industry_median_net_margin` | float | ratio | 行业中位数净利率 |
| `industry_median_roe` | float | ratio | 行业中位数 ROE |
| `revenue_growth_vs_peers_pct` | float | ratio | 收入增速超过同业的百分位 |
| `pe_vs_peers_pct` | float | ratio | PE 高于同业的百分位 |

**confidence 赋值规则：**
- 默认 1.0
- 同业公司数 < 5 → confidence *= 0.70
- 无行业对标数据 → data_quality=unavailable, domain_payload 中行业比较字段为 unknown

#### 3.2.8 capital_allocation_metrics

```
evidence_type: "capital_allocation_metrics"
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: 财务报表 API（cash_flow_statement, balance_sheet），需 ≥3 年历史
获取频率: 季度
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `capex_to_revenue_ttm` | float | ratio | CapEx / Revenue |
| `rd_to_revenue_ttm` | float | ratio | R&D / Revenue |
| `buyback_yield_ttm` | float | ratio | 净回购 / Market Cap |
| `dividend_payout_ratio` | float | ratio | 分红 / Net Income |
| `total_shareholder_return_yield` | float | ratio | (Buyback + Dividend) / Market Cap |
| `asset_turnover` | float | ratio | Revenue / Total Assets |
| `capex_efficiency_ratio` | float | ratio | Revenue Growth / CapEx to Revenue（增量效率） |

**facts 字段：**
| fact | 类型 | 说明 |
|------|------|------|
| `growth_capex_flag` | bool | CapEx 显著增加且指向产能扩张 |

**growth_capex_flag 计算规则（SPEC-004 §20）：**
```
growth_capex_flag = (
    capex_to_revenue_ttm > 3y_avg_capex_to_revenue * 1.3
    AND revenue_growth_ttm > 0
    AND NOT derived_from_macro_label("capex_cycle_stage")
)
```
不得仅根据 Macro/Meso 的 `capex_cycle_stage` label 推断该值。

**confidence 赋值规则：** 默认 1.0。

#### 3.2.9 earnings_quality_metrics

```
evidence_type: "earnings_quality_metrics"
generation_type: structured
determinism_level: structured
can_support_hard_constraint: false
数据来源: 财务报表 API（income_statement, cash_flow_statement），需 ≥2 年历史
获取频率: 季度
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `accruals_to_assets` | float | ratio | 应计项目 / 总资产 |
| `cashflow_to_net_income` | float | ratio | 经营 CF / 净利润 |
| `revenue_to_cashflow_gap` | float | ratio | （收入增速 - CF 增速）的绝对值 |
| `one_time_items_ratio` | float | ratio | 一次性项目 / Net Income |
| `dsri` | float | ratio | 应收账款周转天数指数（Beneish M-score 分量） |

**labels 字段：**
| label | 取值 | 说明 |
|-------|------|------|
| `earnings_quality` | high / medium / low / unknown | 综合盈利质量标签 |

**earnings_quality 分类规则（确定性决策树）：**
```
if all metrics available:
    score = 0
    if accruals_to_assets < 0.05: score += 1
    if cashflow_to_net_income > 1.0: score += 1
    if revenue_to_cashflow_gap < 0.10: score += 1
    if one_time_items_ratio < 0.05: score += 1
    if dsri < 1.2: score += 1
    
    if score >= 4: earnings_quality = "high"
    elif score >= 2: earnings_quality = "medium"
    else: earnings_quality = "low"
else:
    earnings_quality = "unknown"
```

**confidence 赋值规则：**
- 默认取模型自评分 0.80（structured，SPEC-005 §4.4.2）
- 历史数据 < 2 年 → confidence *= 0.60
- 一次性项目数据缺失 → confidence *= 0.85

---

## 4. Metric Catalog

从 SPEC-004 §20 的 13 个 constraint_exports metrics 出发，定义每个 metric 的完整规格。

### 4.1 Metric 汇总

| # | metric_id | 公式类型 | 单位 | can_support_hard | 来源 Evidence |
|---|---|---|---|---|---|
| 1 | `revenue_growth_ttm` | 确定性公式 | ratio | true | financial_metrics |
| 2 | `industry_median_revenue_growth_ttm` | 查询 | ratio | true | peer_comparison_metrics |
| 3 | `gross_margin_ttm` | 确定性公式 | ratio | true | financial_metrics |
| 4 | `gross_margin_qoq_change` | 确定性公式 | ratio | true | margin_metrics |
| 5 | `operating_margin_ttm` | 确定性公式 | ratio | true | margin_metrics |
| 6 | `fcf_margin_ttm` | 确定性公式 | ratio | true | cashflow_metrics |
| 7 | `net_debt_to_ebitda` | 确定性公式 | ratio | true | balance_sheet_metrics |
| 8 | `roe_ttm` | 确定性公式 | ratio | true | financial_metrics |
| 9 | `roic_ttm` | 确定性公式 | ratio | true | financial_metrics |
| 10 | `pe_percentile_5y` | 确定性公式 | ratio | true | valuation_metrics |
| 11 | `ev_ebitda_percentile_5y` | 确定性公式 | ratio | true | valuation_metrics |
| 12 | `fcf_yield` | derived | ratio | true | cashflow_metrics + market_data（跨 Evidence） |
| 13 | `growth_capex_flag` | 确定性规则 | bool | true | capital_allocation_metrics |

### 4.2 每个 Metric 的完整定义

#### metric://revenue_growth_ttm

**公式：**
```
revenue_growth_ttm = (sum(revenue[Q_t-3..Q_t]) - sum(revenue[Q_t-7..Q_t-4])) 
                     / sum(revenue[Q_t-7..Q_t-4])
其中 Q_t = 最近完整季度
负值表示收入下降
```

**输入数据：** 季度财务报表 `revenue` 字段，需最近 8 个季度

**AlphaDB/tinydata 字段映射：** `fina_income.operating_revenue`（营业收入）/ `td.fina_income()` → `operating_revenue`。A 股利润表的 "营业收入" 与美股 "Revenue" 语义一致，均为不含税营业总收入。

**Metric Registry 条目：**
```json
{
  "metric_id": "revenue_growth_ttm",
  "display_name": "TTM 收入增速",
  "description": "过去四个季度的总收入同比增长率。反映公司收入的整体增长态势。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "financial_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "revenue_growth_ttm",
  "expected_export_ref": "metric://revenue_growth_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "财报数据 > 90 天: ×0.85",
      "财报数据 > 180 天: ×0.70",
      "数据重述: ×0.90"
    ]
  },
  "tags": ["growth", "revenue", "fundamentals", "hard_constraint"]
}
```

#### metric://industry_median_revenue_growth_ttm

**公式：**
```
industry_median_revenue_growth_ttm = median(
    [revenue_growth_ttm(peer_i) for peer_i in industry_peers]
)
其中 industry_peers 从行业对标 DB 获取
```

**输入数据：** 行业对标 DB 中的同业公司 revenue_growth_ttm 值

**AlphaDB/tinydata 字段映射：** AlphaDB `rawdata.index_swmember`（申万行业成分） → peer list → SQL 聚合 peer `fina_income.operating_revenue` 计算 industry_median。tinydata 需 `td.stock_industry_versioned()` 获取行业 peer list 后应用层聚合。

**Metric Registry 条目：**
```json
{
  "metric_id": "industry_median_revenue_growth_ttm",
  "display_name": "行业中位数 TTM 收入增速",
  "description": "同行业内所有公司的 TTM 收入增速中位数。用于判断公司在行业中的相对增长位置。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_peer_v1",
  "producing_capability": "cap_peer_comparison_compute",
  "evidence_type": "peer_comparison_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "industry_median_revenue_growth_ttm",
  "expected_export_ref": "metric://industry_median_revenue_growth_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报季后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "同业公司 < 5: ×0.70"
    ]
  },
  "tags": ["growth", "peer_comparison", "fundamentals", "hard_constraint"]
}
```

#### metric://gross_margin_ttm

**公式：**
```
gross_margin_ttm = (sum(gross_profit[Q_t-3..Q_t]) / sum(revenue[Q_t-3..Q_t]))
其中 Q_t = 最近完整季度
```

**输入数据：** 季度财务报表 `gross_profit` 和 `revenue` 字段

**AlphaDB/tinydata 字段映射：** `fina_indicator.grossprofit_margin`（毛利率）可直接取用；或从 `fina_income` 手动计算：`(operating_revenue - operating_cost) / operating_revenue`。

**Metric Registry 条目：**
```json
{
  "metric_id": "gross_margin_ttm",
  "display_name": "TTM 毛利率",
  "description": "过去四个季度的毛利率。反映公司基础盈利能力和定价权。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "financial_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "gross_margin_ttm",
  "expected_export_ref": "metric://gross_margin_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["profitability", "margin", "fundamentals", "hard_constraint"]
}
```

#### metric://gross_margin_qoq_change

**公式：**
```
gross_margin_current_quarter = gross_profit[Q_t] / revenue[Q_t]
gross_margin_prev_quarter = gross_profit[Q_t-1] / revenue[Q_t-1]
gross_margin_qoq_change = gross_margin_current_quarter - gross_margin_prev_quarter
正值表示毛利率环比改善
// NOTE: 这是真正的 QoQ（本季度 vs 前一季度），不是 TTM 变动
```

**输入数据：** 季度财务报表 `gross_profit` 和 `revenue` 字段

**AlphaDB/tinydata 字段映射：** `fina_income.operating_revenue`（营业收入）、`fina_income.operating_cost`（营业成本）。`gross_profit = operating_revenue - operating_cost`。也可直接用 `fina_indicator.grossprofit_margin` 的 QoQ 差值。

**Metric Registry 条目：**
```json
{
  "metric_id": "gross_margin_qoq_change",
  "display_name": "毛利率环比变动",
  "description": "当前季度毛利率与前一季度的变动幅度。正值表示改善，负值表示恶化。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "margin_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "gross_margin_qoq_change",
  "expected_export_ref": "metric://gross_margin_qoq_change",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["profitability", "margin", "momentum", "fundamentals", "hard_constraint"]
}
```

#### metric://operating_margin_ttm

**公式：**
```
operating_margin_ttm = sum(operating_income[Q_t-3..Q_t]) / sum(revenue[Q_t-3..Q_t])
```

**AlphaDB/tinydata 字段映射：** AlphaDB `fina_income.operating_income`（营业利润） / `fina_income.operating_revenue`（营业收入）。A 股 CAS 利润表中 "营业利润" 近似等于 EBIT（息税前利润）。也可用 `fina_indicator.` 字段（综合指标表可能直接提供经营利润率）。

**Metric Registry 条目：**
```json
{
  "metric_id": "operating_margin_ttm",
  "display_name": "TTM 经营利润率",
  "description": "过去四个季度的经营利润率（EBIT/Revenue）。反映公司核心业务的盈利能力。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "margin_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "operating_margin_ttm",
  "expected_export_ref": "metric://operating_margin_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["profitability", "margin", "fundamentals", "hard_constraint"]
}
```

#### metric://fcf_margin_ttm

**公式：**
```
fcf_ttm = sum(operating_cashflow[Q_t-3..Q_t]) - sum(capex[Q_t-3..Q_t])
fcf_margin_ttm = fcf_ttm / sum(revenue[Q_t-3..Q_t])
```

**AlphaDB/tinydata 字段映射：** AlphaDB `fina_cashflow.n_cashflow_act`（经营活动现金流净额）+ `fina_cashflow.c_cap_ex`（资本开支）→ FCF。`fcf_ttm` 来自 §3.2.4 cashflow_metrics，`revenue` 来自 §3.2.1 financial_metrics。

**Metric Registry 条目：**
```json
{
  "metric_id": "fcf_margin_ttm",
  "display_name": "TTM 自由现金流率",
  "description": "过去四个季度的 FCF/Revenue。反映公司将收入转化为可支配现金的能力。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_cashflow_v1",
  "producing_capability": "cap_cashflow_metric_compute",
  "evidence_type": "cashflow_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "fcf_margin_ttm",
  "expected_export_ref": "metric://fcf_margin_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["cashflow", "quality", "fundamentals", "hard_constraint"]
}
```

#### metric://net_debt_to_ebitda

**公式：**
```
net_debt = total_debt - cash_and_equivalents
ebitda_ttm = sum(ebitda[Q_t-3..Q_t])
net_debt_to_ebitda = net_debt / ebitda_ttm
若 ebitda_ttm <= 0 → net_debt_to_ebitda = null, 标记为 negative_ebitda
```

**AlphaDB/tinydata 字段映射：** AlphaDB `fina_balancesheet.total_liability`（总负债）、`fina_balancesheet.money_cap`（货币资金）→ net_debt。EBITDA 需从 `fina_income` 手动计算（营业利润 + 折旧摊销，A 股 CAS 的 EBITDA 常不直接在表中列示）。tinydata 同理。金融机构（银行/保险/券商）不适用此指标 → §3.2.5 confidence 规则已标注。

**Metric Registry 条目：**
```json
{
  "metric_id": "net_debt_to_ebitda",
  "display_name": "净负债 / EBITDA",
  "description": "净负债（总负债减现金）除以 TTM EBITDA。衡量公司杠杆水平和偿债能力。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_balance_v1",
  "producing_capability": "cap_balance_sheet_compute",
  "evidence_type": "balance_sheet_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "net_debt_to_ebitda",
  "expected_export_ref": "metric://net_debt_to_ebitda",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "金融机构: ×0.70（杠杆指标不适用于金融股）"
    ]
  },
  "tags": ["leverage", "risk", "fundamentals", "hard_constraint"]
}
```

#### metric://roe_ttm

**公式：**
```
net_income_ttm = sum(net_income[Q_t-3..Q_t])
avg_equity = (total_equity[t] + total_equity[t-4]) / 2
roe_ttm = net_income_ttm / avg_equity
若 avg_equity <= 0 → roe_ttm = null
```

**AlphaDB/tinydata 字段映射：** `fina_indicator.roe_dt`（归母扣非加权 ROE）。A 股 ROE 常用归母口径而非合并口径。若需手动计算：`net_profit_parent_ttm / avg(total_equity_parent)`。

**Metric Registry 条目：**
```json
{
  "metric_id": "roe_ttm",
  "display_name": "TTM ROE",
  "description": "过去四个季度的净资产收益率。DuPont 分解可用于进一步分析。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "financial_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "roe_ttm",
  "expected_export_ref": "metric://roe_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["profitability", "return", "fundamentals", "hard_constraint"]
}
```

#### metric://roic_ttm

**公式：**
```
nopat_ttm = sum(operating_income[Q_t-3..Q_t]) * (1 - effective_tax_rate)
invested_capital = total_debt + total_equity - cash_and_equivalents
roic_ttm = nopat_ttm / avg(invested_capital[t], invested_capital[t-4])
```

**AlphaDB/tinydata 字段映射：** 需组合多表：`fina_income.operating_income`（营业利润）→ NOPAT；`fina_balancesheet`（total_liability + total_equity - money_cap）→ invested_capital。有效税率取 `fina_income.income_tax / total_profit`。A 股 CAS 无标准 ROIC 字段，必须手动计算。`fina_indicator` 可能直接提供近似 ROIC。

**Metric Registry 条目：**
```json
{
  "metric_id": "roic_ttm",
  "display_name": "TTM ROIC",
  "description": "投入资本回报率。衡量公司对所有投入资本（债务+权益）的使用效率。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_financial_v1",
  "producing_capability": "cap_financial_metric_compute",
  "evidence_type": "financial_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "roic_ttm",
  "expected_export_ref": "metric://roic_ttm",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度财报发布后 45 天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["profitability", "return", "efficiency", "fundamentals", "hard_constraint"]
}
```

#### metric://pe_percentile_5y

**公式：**
```
historical_pe = [pe_t, pe_t-1, ..., pe_t-1259]  // 5 年日序列，约 1260 个交易日
pe_current = market_cap / net_income_ttm
pe_percentile_5y = count(v <= pe_current for v in historical_pe) / len(historical_pe)
范围 [0.0, 1.0]，0.0 = 历史最低，1.0 = 历史最高
若 historical_pe 长度 < 756 (3 年) → 降级
若 net_income_ttm <= 0 → null
```

**AlphaDB/tinydata 字段映射：** `stock_dailybasic.pe_ttm`（每日 PE-TTM，总市值/归母净利润 TTM）。历史序列直接从 stock_dailybasic 日线提取最近 1250 个交易日（约 5 年），剔除停牌日。

**Metric Registry 条目：**
```json
{
  "metric_id": "pe_percentile_5y",
  "display_name": "5 年 PE 分位",
  "description": "当前 PE（TTM）在过去 5 年日 PE 序列中的百分位。0.0 表示历史最低，1.0 表示历史最高。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_valuation_v1",
  "producing_capability": "cap_valuation_compute",
  "evidence_type": "valuation_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "pe_percentile_5y",
  "expected_export_ref": "metric://pe_percentile_5y",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 5,
    "valid_until_rule": "next_trading_day",
    "description": "每个交易日更新"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "历史序列 < 3 年: ×0.75",
      "负盈利（PE 无意义）: ×0.70",
      "估值数据 > 5 交易日未更新: ×0.90"
    ]
  },
  "tags": ["valuation", "percentile", "fundamentals", "hard_constraint"]
}
```

#### metric://ev_ebitda_percentile_5y

**公式：**
```
ev = market_cap + total_debt - cash_and_equivalents
ev_ebitda_current = ev / ebitda_ttm
ev_ebitda_percentile_5y = percentile(ev_ebitda_current, historical_ev_ebitda_sequence_5y)
若 ebitda_ttm <= 0 → null
```

**AlphaDB/tinydata 字段映射：** 同 `pe_percentile_5y`（§4.2 metric://pe_percentile_5y）。EV 组合：`market_cap`（`stock_dailybasic.total_mv`）+ `total_debt - cash`（`fina_balancesheet`）。历史 EV/EBITDA 序列从 `stock_dailybasic` + `fina_balancesheet` + `fina_income` 组合重建。A 股 EBITDA 常不在表中直接列示，需营业利润 + 折旧摊销手动推导。

**Metric Registry 条目：**
```json
{
  "metric_id": "ev_ebitda_percentile_5y",
  "display_name": "5 年 EV/EBITDA 分位",
  "description": "当前 EV/EBITDA 在过去 5 年日序列中的百分位。PE 的补充指标，排除资本结构影响。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_valuation_v1",
  "producing_capability": "cap_valuation_compute",
  "evidence_type": "valuation_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "ev_ebitda_percentile_5y",
  "expected_export_ref": "metric://ev_ebitda_percentile_5y",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 5,
    "valid_until_rule": "next_trading_day",
    "description": "每个交易日更新"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算"
  },
  "tags": ["valuation", "percentile", "fundamentals", "hard_constraint"]
}
```

#### metric://fcf_yield

**公式：**
```
fcf_ttm = sum(operating_cashflow[Q_t-3..Q_t]) - sum(capex[Q_t-3..Q_t])
fcf_yield = fcf_ttm / market_cap
若 fcf_ttm <= 0 → fcf_yield = null, 标记 negative_fcf

// fcf_yield 是 derived metric：现金流来自 cashflow_metrics，市值来自 market_data（行情 API）
// MVP 兼容：ConstraintExport.evidence_ref 指向承载该值的 valuation_metrics Evidence Packet
//   valuation_metrics EP 必须在 limitations 中记录其 lineage（cashflow_metrics + market_data）
// Post-MVP：评估是否需要向 SPEC-004 提变更，为 ConstraintExport 增加 source_evidence_refs 字段
// 若 market_data 不可用 → fcf_yield = null → 不可作为 Hard Constraint 支撑
```

**AlphaDB/tinydata 字段映射：** FCF = `sum(fina_cashflow.n_cashflow_act[4Q]) - sum(fina_cashflow.c_cap_ex[4Q])`，市值 = `stock_dailybasic.total_mv / 10000`（万元→元）。tinydata 需组合调用 `td.fina_cashflow()` + `td.stock_daily()`。

**Metric Registry 条目：**
```json
{
  "metric_id": "fcf_yield",
  "display_name": "自由现金流收益率",
  "description": "TTM FCF / 市值。衡量以当前价格买入时，公司产生自由现金流的回报率。Derived metric：FCF 来自 cashflow_metrics，市值来自 market_data。",
  "value_type": "number",
  "unit": "ratio",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_valuation_v1",
  "producing_capability": "cap_valuation_compute",
  "evidence_type": "valuation_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "fcf_yield",
  "expected_export_ref": "metric://fcf_yield",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 5,
    "valid_until_rule": "next_trading_day",
    "description": "每个交易日更新（市值变化）"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "market_data 不可用: ×0.0（null）",
      "fcf_ttm <= 0: ×0.0（null）"
    ]
  },
  "lineage_constraints": {
    "requires_source_event_ref": false,
    "description": "TTM FCF / 市值。Derived metric：FCF 来自 cashflow_metrics，市值来自 market_data（行情 API）。衡量以当前价格买入时，公司产生自由现金流的回报率。"
  },
  "tags": ["valuation", "cashflow", "yield", "fundamentals", "hard_constraint", "derived"]
}
```

#### metric://growth_capex_flag

**公式：**
```
growth_capex_flag = (
    capex_to_revenue_ttm > 3y_avg_capex_to_revenue * 1.3
    AND revenue_growth_ttm > 0
)
// boolean: true = 公司级数据充分且确定是 growth capex；false = 公司级数据充分且确定不是 growth capex
// 若 fundamentals-only 数据不足以判断（如 CapEx 含一次性项目无法分离、
//   或需 Macro/Meso 的 capex_cycle_stage label 才能判断）：
//     growth_capex_flag = null（标记 unavailable）
//     can_support_hard_constraint = false
//     add warning: "insufficient_company_level_capex_evidence"
//     constraint_export 不导出 growth_capex_flag
//
// constrained_by SPEC-004 §20：不得仅根据 Macro/Meso 的 capex_cycle_stage label 推断该值
// 具体含义：
//   - 独立判断 → true 或 false（都合法）
//   - 依赖 macro label → null（不可判定，不导出）
//   - false ≠ unknown — false 意味着"经过检查且确定不足"，不是"不知道"
```

**AlphaDB/tinydata 字段映射：** AlphaDB `fina_cashflow.c_cap_ex`（资本开支）+ `fina_income.operating_revenue`（营业收入）→ capex_to_revenue_ttm。3y_avg 从历史 12 季度 `fina_cashflow` 和 `fina_income` 聚合。tinydata 需 `td.fina_cashflow()` + `td.fina_income()` 取历史数据。注意：A 股 CAS 的 CapEx 编码为 `c_cap_ex`（购建固定资产、无形资产和其他长期资产支付的现金）。

**Metric Registry 条目：**
```json
{
  "metric_id": "growth_capex_flag",
  "display_name": "增长型资本开支标志",
  "description": "仅在公司级 CapEx 显著增长、收入正增长、且判断独立于宏观 label 时为 true。",
  "value_type": "boolean",
  "unit": "",
  "metric_category": "computed",
  "source_domain": "fundamentals",
  "producing_package": "pkg_fundamentals_capital_v1",
  "producing_capability": "cap_capital_allocation_compute",
  "evidence_type": "capital_allocation_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "growth_capex_flag",
  "expected_export_ref": "metric://growth_capex_flag",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_45_days",
    "description": "每季度更新"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "若 CapEx 数据含一次性项目且无法分离: growth_capex_flag = null（不导出）",
      "若需 Macro label 才能判断: growth_capex_flag = null（不导出）"
    ]
  },
  "tags": ["capex", "growth", "boolean", "fundamentals", "hard_constraint"]
}
```

---

## 5. Internal Pipeline

```
function run_fundamentals_domain(job: AnalysisDomainJob) -> AnalysisCard:

    // ═══ Step 1: Input Filtering (computed) ═══
    required_evidence_types = [
        "financial_metrics", "growth_metrics", "margin_metrics",
        "cashflow_metrics", "balance_sheet_metrics", "valuation_metrics"
    ]
    optional_evidence_types = [
        "peer_comparison_metrics", "capital_allocation_metrics",
        "earnings_quality_metrics"
    ]

    available_evidence = filter_evidence_by_domain(job.evidence_refs, domain="fundamentals")
    missing_required = required_evidence_types - types_of(available_evidence)

    if len(missing_required) >= 3:
        return unavailable_card(
            domain_status="unavailable",
            domain_status_reason="insufficient_data",
            missing_required_evidence=missing_required
        )

    if len(missing_required) >= 1:
        // partial — can proceed with limited analysis
        domain_status = "partial"

    // ═══ Step 2: Deterministic Metric Computation (computed) ═══
    financial_metrics = extract_metrics(available_evidence, "financial_metrics")
    growth_metrics = extract_metrics(available_evidence, "growth_metrics")
    margin_metrics_val = extract_metrics(available_evidence, "margin_metrics")
    cashflow_metrics = extract_metrics(available_evidence, "cashflow_metrics")
    balance_metrics = extract_metrics(available_evidence, "balance_sheet_metrics")
    valuation_metrics_val = extract_metrics(available_evidence, "valuation_metrics")

    // Each metric formula defined in §4 Metric Catalog
    computed = {
        "revenue_growth_ttm": compute_revenue_growth_ttm(financial_metrics),
        "gross_margin_ttm": compute_gross_margin_ttm(financial_metrics),
        "gross_margin_qoq_change": compute_gross_margin_qoq(margin_metrics_val),
        "operating_margin_ttm": compute_operating_margin(margin_metrics_val),
        "fcf_margin_ttm": compute_fcf_margin(cashflow_metrics),
        "net_debt_to_ebitda": compute_net_debt_to_ebitda(balance_metrics),
        "roe_ttm": compute_roe(financial_metrics),
        "roic_ttm": compute_roic(financial_metrics),
        "pe_percentile_5y": compute_pe_percentile(valuation_metrics_val),
        "ev_ebitda_percentile_5y": compute_ev_ebitda_percentile(valuation_metrics_val),
        "fcf_yield": compute_fcf_yield(cashflow_metrics, valuation_metrics_val),
        "growth_capex_flag": compute_growth_capex_flag(
            extract_metrics(available_evidence, "capital_allocation_metrics"),
            financial_metrics
        ),
        // optional: peer comparison
        "industry_median_revenue_growth_ttm": compute_or_null(
            available_evidence, "peer_comparison_metrics",
            "industry_median_revenue_growth_ttm"
        ),
    }

    // ═══ Step 3: Structured Quality Classification (structured) ═══
    growth_quality = classify_growth_quality(computed)
    profitability_quality = classify_profitability(computed)
    cashflow_quality = classify_cashflow_quality(computed)
    balance_sheet_risk = classify_balance_sheet_risk(computed)
    valuation_state = classify_valuation_state(computed)
    capital_allocation_quality = classify_capital_allocation(
        available_evidence, computed
    )

    // Optional: earnings quality
    earnings_quality = classify_earnings_quality(available_evidence)

    // Classification rules defined in §7 + §3.2.9
    // All five are deterministic rule-based, no LLM

    // ═══ Step 4: Internal Computation Results Assembly ═══
    // Consolidate all computed metrics and structured labels for card assembly.
    // NOTE: This is IN-MEMORY CONSOLIDATION only — no first-class Evidence Packets
    // are created or written back to the shared Evidence Pool.
    // If other domains need these values, request through Orchestrator evidence request.
    computed_metrics = { ... all computed values from Step 2 }
    structured_labels = {
        "growth_quality": growth_quality,
        "profitability_quality": profitability_quality,
        "cashflow_quality": cashflow_quality,
        "balance_sheet_risk": balance_sheet_risk,
        "valuation_state": valuation_state,
        "earnings_quality": earnings_quality,
        "capital_allocation_quality": capital_allocation_quality,
    }
    // confidence values per evidence type per §3.2 degradation rules

    // ═══ Step 5: Stance Determination (computed from structured) ═══
    stance = determine_stance(
        growth_quality, profitability_quality, cashflow_quality,
        balance_sheet_risk, valuation_state
    )
    // Stance rules defined in §7

    // ═══ Step 6: Confidence Computation (computed) ═══
    confidence = compute_domain_confidence(available_evidence, structured_labels)
    // Confidence model defined in §8

    // ═══ Step 7: Analysis Card Assembly ═══
    card = build_analysis_card(
        job=job,
        domain_status=domain_status,
        domain_status_reason=infer_reason(domain_status, missing_required),
        available_evidence=available_evidence,
        stance=stance,
        confidence=confidence,
        computed_metrics=computed,
        structured_labels=structured_labels,
        supporting_evidence=filter_positive(available_evidence),
        opposing_evidence=filter_negative(available_evidence),
        constraint_exports=build_exports(computed, available_evidence),
        domain_payload=build_payload(structured_labels, computed),
        data_freshness=compute_freshness(available_evidence),
        key_risks=derive_key_risks(structured_labels, computed),
        invalidating_conditions=derive_invalidating_conditions(structured_labels),
        warnings=derive_warnings(missing_required, available_evidence)
    )

    // ═══ Step 8: Domain-Level Validation ═══
    card = run_domain_validation(card)
    // Validation rules defined in §10

    // ═══ Step 9 (MVP): Summary & Key Findings Generation (interpreted) ═══
    // MVP: may use template placeholders
    if job.run_config.depth != "quick":
        card.summary = generate_summary(card)          // LLM, interpreted
        card.key_findings = generate_key_findings(card) // LLM, interpreted
    else:
        card.summary = template_summary(card)          // deterministic template
        card.key_findings = template_key_findings(card)

    return card
```

**管线步骤 generation_type 标注：**

| 步骤 | generation_type | determinism_level |
|------|:---:|:---:|
| Step 1: Input Filtering | computed | computed |
| Step 2: Metric Computation | computed | computed |
| Step 3: Quality Classification | structured | structured |
| Step 4: Internal Results Consolidation | computed | computed |
| Step 5: Stance Determination | computed | computed |
| Step 6: Confidence Computation | computed | computed |
| Step 7: Card Assembly | computed | computed |
| Step 8: Domain Validation | computed | computed |
| Step 9: Summary (quick depth) | computed | computed |
| Step 9: Summary (standard/deep) | interpreted | interpreted |

---

## 6. Determinism Map

| 管线步骤 | generation_type | determinism_level | 实现方式 | 可单测 |
|---------|:---:|:---:|------|:---:|
| 财务指标计算（13 个 metrics） | computed | computed | 确定性数学公式 | ✅ |
| 估值分位计算 | computed | computed | 历史序列百分位 | ✅ |
| growth_quality 分类 | structured | structured | 决策树（规则模型） | ✅ |
| profitability_quality 分类 | structured | structured | 决策树 | ✅ |
| cashflow_quality 分类 | structured | structured | 决策树 | ✅ |
| balance_sheet_risk 分类 | structured | structured | 决策树 | ✅ |
| valuation_state 分类 | structured | structured | 规则模型 | ✅ |
| capital_allocation_quality 分类 | structured | structured | 决策树 | ✅ |
| earnings_quality 分类 | structured | structured | 决策树（§3.2.9） | ✅ |
| stance 聚合 | computed | computed | 加权打分（§7） | ✅ |
| confidence 聚合 | computed | computed | 加权平均（§8） | ✅ |
| summary 生成 | interpreted | interpreted | LLM（MVP 可模板占位） | ❌ |
| key_findings 生成 | interpreted | interpreted | LLM（MVP 可模板占位） | ❌ |
| invalidating_conditions | interpreted | interpreted | LLM + 结构化规则 | 部分 |
| key_risks 生成 | interpreted | interpreted | LLM + 结构化规则 | 部分 |

---

## 7. Stance Logic

Fundamentals 的 stance 来自 5 个子信号的加权组合。

### 7.1 子信号 → 子 stance 映射

**ClassifyGrowthQuality(growth_quality, revenue_growth_ttm, industry_median):**

```
strong  → sub_stance = "positive"
medium  → sub_stance = "moderately_positive"
weak    → sub_stance = "moderately_negative"
deteriorating → sub_stance = "negative"
unknown → sub_stance = "neutral"
```

**ClassifyProfitabilityQuality(profitability_quality, gross_margin_ttm, operating_margin_ttm):**

```
high    → sub_stance = "positive"
medium  → sub_stance = "moderately_positive"
low     → sub_stance = "moderately_negative"
deteriorating → sub_stance = "negative"
unknown → sub_stance = "neutral"
```

**ClassifyCashflowQuality(cashflow_quality, fcf_margin_ttm, fcf_yield):**

```
strong  → sub_stance = "positive"
medium  → sub_stance = "moderately_positive"
weak    → sub_stance = "moderately_negative"
negative → sub_stance = "negative"
unknown → sub_stance = "neutral"
```

**ClassifyBalanceSheetRisk(balance_sheet_risk, net_debt_to_ebitda):**

```
low     → sub_stance = "positive"
medium  → sub_stance = "moderately_negative"
high    → sub_stance = "negative"
unknown → sub_stance = "neutral"
```

**ClassifyValuationState(valuation_state, pe_percentile_5y, ev_ebitda_percentile_5y):**

```
cheap        → sub_stance = "positive"
reasonable   → sub_stance = "moderately_positive"
expensive    → sub_stance = "moderately_negative"
very_expensive → sub_stance = "negative"
unknown      → sub_stance = "neutral"
```

### 7.2 子 stance 聚合为整体 stance

```
function determine_stance(sub_stances: list[(string, float)]) -> Stance:
    // sub_stances: list of (sub_stance_label, weight)
    // 权重: growth=0.25, profitability=0.25, cashflow=0.20, balance_sheet=0.15, valuation=0.15

    score = 0
    for (label, weight) in sub_stances:
        if label == "positive": score += 1.0 * weight
        elif label == "moderately_positive": score += 0.5 * weight
        elif label == "neutral": score += 0.0 * weight
        elif label == "moderately_negative": score += -0.5 * weight
        elif label == "negative": score += -1.0 * weight

    total_weight = sum(weight for (_, weight) in sub_stances)
    if total_weight == 0:
        return Stance.UNAVAILABLE

    normalized = score / total_weight

    if normalized >= 0.6: return Stance.POSITIVE
    elif normalized >= 0.2: return Stance.MODERATELY_POSITIVE
    elif normalized >= -0.2: return Stance.MIXED
    elif normalized >= -0.6: return Stance.MODERATELY_NEGATIVE
    else: return Stance.NEGATIVE
```

**边界值定义：**

| score 范围 | stance | 边界归属 |
|-----------|--------|---------|
| normalized ≥ 0.6 | positive | 0.6 inclusive |
| 0.2 ≤ normalized < 0.6 | moderately_positive | 0.6 exclusive, 0.2 inclusive |
| -0.2 ≤ normalized < 0.2 | mixed | 0.2 exclusive, -0.2 inclusive |
| -0.6 ≤ normalized < -0.2 | moderately_negative | -0.2 exclusive, -0.6 inclusive |
| normalized < -0.6 | negative | -0.6 exclusive |

> 注意：此表使用 `>=`/`<` 语义，与上面 `if/elif` 的 `>=`/`elif` 链完全等价。阈值边界归属由 `>=` 运算符直接确定——达到阈值则归属于较高的 stance。

### 7.3 不可用处理

如果 ≥3 个子信号为 unknown：
```
stance = "unavailable"
domain_status = downgrade_domain_status(domain_status, target="partial")
// downgrade 规则（只允许降级，不允许升级）：
//   completed → partial
//   partial  → partial（不变）
//   error    → error（不参与 downgrade chain，error 不可自动恢复）
//   unavailable → unavailable（不变）
```

---

## 8. Confidence Model

### 8.1 公式

```
confidence = (
    evidence_confidence_avg * 0.60 +
    completeness_factor * 0.25 +
    data_freshness_factor * 0.15
) * domain_status_multiplier
```

### 8.2 子项定义

**evidence_confidence_avg:**
```
平均所有可用的 computed + structured Evidence Packet 的 confidence 值
纯 computed evidence: confidence = 1.0（降级后按 §3.2 规则）
structured evidence: confidence = 模型自评分（§3.2.9）
若某类 evidence 缺失 → 该项不参与平均
```

**completeness_factor:**
```
所有 9 种 Evidence Packet 类型中可用的占比
completeness = count(available_types) / 9
completeness_factor = clamp(completeness, 0.0, 1.0)
```

**data_freshness_factor:**
```
基于最旧 evidence 的 as_of 距今天数:
  ≤ 90 天  → 1.0
  ≤ 180 天 → 0.70
  > 180 天 → 0.40
```

**domain_status_multiplier:**
```
completed   → 1.0
partial     → 0.80
error       → 0.0
unavailable → 0.0
```

### 8.3 最终截断

```
confidence = min(confidence, confidence_cap_from_quality(data_quality))
// data_quality → confidence cap 映射（SPEC-013 自定义，待与 SPEC-004/009 对齐）：
//   high → 0.85, medium → 0.70, low → 0.45, unavailable → 0.20, unknown → 0.50
// 注意：此映射目前仅在 SPEC-013 中定义。如果 SPEC-004 或 SPEC-009 后续定义了
// 全局统一的 data_quality → confidence_cap 映射，本映射应被替换。
```

### 8.4 MVP 简化

如果 `earnings_quality_metrics` 不可用（MVP 可选）：`completeness_factor` 分母调整为 8（而非 9），且 `earnings_quality` 在 domain_payload 中标记为 `unknown`。

---

## 9. Card Assembly

| 字段 | 填充来源 | 规则 |
|------|---------|------|
| `card_id` | 系统生成 | `card_fundamentals_{task_id}` |
| `schema_version` | 固定 | `SPEC-004@0.2.7` |
| `task_id` | job.task_id | 直传 |
| `run_id` | job.run_id | 直传 |
| `domain` | 固定 | `fundamentals` |
| `domain_status` | 管线执行结果 | completed / partial / error / unavailable |
| `domain_status_reason` | 当 status ∈ {error, unavailable} 时必填；当 status = partial 时推荐填写 | insufficient_data / execution_failure / data_source_unavailable / skipped_by_config |
| `domain_status_reason` 补充规则 | partial 可选但推荐：当 partial 是由 missing data、stale data、或 unsupported metric 导致时，填写对应 reason；completed 时 domain_status_reason 必须为 null | — |
| `summary` | LLM 或模板 | standard/deep: LLM; quick: 模板 |
| `stance` | §7 Stance Logic | — |
| `confidence` | §8 Confidence Model | [0.0, 1.0]，受双重 cap |
| `confidence_reason` | §8 子项明细 | 列出 evidence_confidence, completeness, freshness 贡献 |
| `time_horizon` | 固定 | "6-24 months"（Fundamentals 分析的时间框架） |
| `time_horizon_bucket` | 固定 | `long_term` |
| `supporting_evidence` | Evidence Packets 中 signal ∈ {positive} | 每项引用 evidence_id + 一句话描述 |
| `opposing_evidence` | Evidence Packets 中 signal ∈ {negative} | 必须 ≥1 项（若 stance ∈ directional/mixed） |
| `constraint_exports` | §4 Metric Catalog 中 can_support_hard=true 的 metrics | 每个 export 必须声明 can_support_hard_constraint |
| `domain_payload` | SPEC-004 §19 枚举值 | growth_quality, profitability_quality, cashflow_quality, balance_sheet_risk, valuation_state, earnings_quality, capital_allocation_quality, fundamental_tailwinds, fundamental_headwinds, must_watch_metrics |
| `data_freshness` | 所有 Evidence Packets 的 as_of | 最旧 → oldest_evidence_as_of, 最新 → newest_evidence_as_of |
| `evidence_coverage` | 管线结果 | supporting/opposing count + missing_required_evidence |
| `key_findings` | LLM 或模板 | 2-5 条，每条 1 句话 |
| `key_risks` | §7 子信号 + LLM 补充 | 估值风险、增长放缓风险、现金流恶化风险、杠杆风险 |
| `invalidating_conditions` | 结构化规则 + LLM 补充 | 如 "下季度收入增速 < 0"、"FCF 转负" |
| `warnings` | §10 域级验证 | 数据过期、数据缺失、估值不可用等 |
| `limitations` | 管线执行日志 | 如 "pe_percentile 因负盈利不可用" |
| `created_at` | 系统时间 | ISO 8601 |

---

## 10. Domain Validation

超出 SPEC-004 §41 通用规则的域级检查。所有检查均为 `flag` 级别（无 `block`——`block` 语义由上游 Post-card Validation 阶段统一处理）。

| # | 检查项 | 触发条件 | 严重度 | 处理 |
|---|---|---|---|---|
| 1 | 财报数据过期 > 90 天 | oldest_evidence_as_of > 90 days ago | flag | 降低 confidence，加入 warnings |
| 2 | 财报数据过期 > 180 天 | oldest_evidence_as_of > 180 days ago | flag | domain_status = partial（降级），移除所有 `can_support_hard_constraint=true` 的 constraint_exports，confidence_cap = min(当前 cap, 0.35)，加入 warnings: "stale_data" |
| 3 | 估值数据缺失 | valuation_metrics 不可用 | flag | 移除 valuation 相关 constraint_exports，valuation_state = unknown |
| 4 | 收入增速与行业增速 lineage 异常 | peer_comparison_metrics 的 industry_median 不是来自独立的行业数据库，而是从公司自身 filing 推导（即 financial_metrics 和 peer_comparison_metrics 共享同一个原始数据源） | flag | 标记 lineage 风险，加入 warnings: "peer_data_not_independent" |
| 5 | completed + 无 supporting_evidence | domain_status=completed 但 supporting=[] | flag | 检查 stance 逻辑（neutral 时可能合法） |
| 6 | growth_capex_flag 无法独立判断 | 公司级 CapEx 数据不足以独立判断（含一次性项目无法分离、或需 Macro label 推断） | flag | growth_capex_flag = null（不导出），can_support_hard_constraint = false，加入 warnings: "insufficient_company_level_capex_evidence" |
| 7 | 负盈利导致 PE 不可用 | net_income_ttm <= 0 | flag | pe_percentile_5y = null，valuation_state 降权重 |
| 8 | 同业公司数不足 | peer_comparison 的 industry_peers < 5 | flag | industry_median 指标置信度标记，加入 warnings |

> **severity 说明：** Domain Validation 不产生 `block` 级 finding。`block` 是 Post-card Validation（SPEC-003 §13）的职责——Domain Validation 只负责 flag + 降级处理。如果域级检查发现不应继续（如全部数据不可用），应直接设置 `domain_status=unavailable`。当 `domain_status=partial` 时，card 仍可进入下游但必须携带 flag + warnings；编排器的 Post-card Validation 可以根据 flag 信息决定是否升级为 block。

---

## 11. Data Source Requirements

### 11.1 数据架构总览

Fundamentals 域采用双数据源 Adapter 架构：

| 数据源 | 角色 | 更新频率 | 项目位置 | 访问方式 |
|--------|------|---------|---------|---------|
| **AlphaDB** | 主力离线数据库 | 日更新（Tushare 同步） | `E:\CodePrograms\alphaHome` | PostgreSQL + `alphahome.providers.AlphaDataTool` |
| **tinydata** | 实时数据补充 | 近实时 | `E:\CodePrograms\tinydata` | `import tinydata as td` |

**核心原则：AlphaDB 为主（历史+批量），tinydata 为辅（实时+PIT 补充）。**

### 11.2 与现有数据源的字段映射

CrossLens 不直接依赖底层数据库 schema。所有数据获取通过统一 Adapter 接口（见 §11A），Adapter 内部完成底层 schema → StandardContract 映射。

#### 11.2.1 财务报表相关表

| 数据需求 | AlphaDB 表 | tinydata API | 更新频率 |
|---------|-----------|-------------|---------|
| 利润表 | `rawdata.fina_income` | `td.fina_income()` | 季度 |
| 资产负债表 | `rawdata.fina_balancesheet` | `td.fina_balancesheet()` | 季度 |
| 现金流量表 | `rawdata.fina_cashflow` | `td.fina_cashflow()` | 季度 |
| 综合财务指标 | `rawdata.fina_indicator` | `td.fina_indicator()` | 季度 |
| 业绩预测 | `rawdata.fina_forecast` | `td.fina_forecast()` | 事件驱动 |
| 业绩快报 | `rawdata.fina_express` | `td.fina_express()` | 事件驱动 |
| PIT 披露日历 | `rawdata.fina_pit_ext` | `td.fina_indicator(as_of_date=...)` | 季度 |

#### 11.2.2 行情与估值相关表

| 数据需求 | AlphaDB 表 | tinydata API | 更新频率 |
|---------|-----------|-------------|---------|
| 日线行情 | `rawdata.stock_daily` | `td.stock_daily()` | 日 |
| 每日估值 | `rawdata.stock_dailybasic` | 组合计算 | 日 |
| 实时行情 | — | `td.realtime_snapshot()` | 实时 |
| TTM 指标 | 需计算 | `td.stock_ttm_indicator()` | 日 |

#### 11.2.3 行业与对标相关表

| 数据需求 | AlphaDB 表 | tinydata API | 更新频率 |
|---------|-----------|-------------|---------|
| 行业分类 | `rawdata.stock_industry_versioned` | `td.stock_industry_versioned()` | 事件驱动 |
| 行业成分 | `rawdata.index_swmember` | — | 事件驱动 |
| 行业行情 | `rawdata.index_swdaily` | — | 日 |
| 分析师覆盖 | `rawdata.stock_report_rc` | — | 事件驱动 |

#### 11.2.4 其他数据

| 数据需求 | AlphaDB 表 | tinydata API | 更新频率 |
|---------|-----------|-------------|---------|
| 分红送配 | `rawdata.stock_dividend` | `td.stock_dividend()` | 事件驱动 |
| 交易日历 | `rawdata.others_calendar` | `td.trade_calendar()` | 年度 |
| 主营业务构成 | — | `td.fina_mainbz()` | 季度 |

### 11.3 数据源选择策略

```text
function select_adapter(requirement: DataRequirement) -> Adapter:
    // 1. 实时行情需求 → tinydata（AlphaDB 为日更新，有 T+1 延迟）
    if requirement.is_realtime:
        return TinyDataAdapter()
    
    // 2. 历史批量查询（≥30 天范围）→ AlphaDB（SQL 聚合效率更高）
    if requirement.date_range_days >= 30:
        if AlphaDBAdapter.is_available():
            return AlphaDBAdapter()
        else:
            return TinyDataAdapter()  // fallback
    
    // 3. 行业对标/聚合查询 → AlphaDB（可直接 SQL JOIN/AGG）
    if requirement.is_aggregate:
        return AlphaDBAdapter()
    
    // 4. PIT 敏感查询 → 任选支持 PIT 的源
    if requirement.requires_pit:
        // AlphaDB 有 fina_pit_ext 专用 PIT 表，tinydata 支持 as_of_date 参数
        return AlphaDBAdapter()  // 优先 AlphaDB（PIT 表更完整）
    
    // 5. 默认 → AlphaDB
    return AlphaDBAdapter()
```

### 11.4 会计制度说明

Fundamentals 域 MVP 仅支持 **A 股上市公司（中国会计准则 CAS）**。

| 维度 | A 股 / CAS | 备注 |
|------|-----------|------|
| 财务报告周期 | 一季报(3/31) + 半年报(6/30) + 三季报(9/30) + 年报(12/31) | 与美股 Q1/Q2/Q3/Q4 周期不同 |
| 财报披露截止日 | 一季报 4/30，半年报 8/31，三季报 10/31，年报 4/30 | 影响 data_freshness 判断 |
| 货币 | CNY（人民币元） | 不做汇率转换 |
| 股票代码格式 | `ts_code`（如 `000001.SZ`, `600519.SH`） | 与 AlphaDB/tinydata 一致 |
| 行业分类 | 申万行业分类（SWHY）为主 | `stock_industry_versioned.src='SW2021'` |
| PE 计算 | PE(TTM) = 总市值 / 归母净利润(TTM) | 与 `stock_dailybasic.pe_ttm` 一致 |
| ROE | 加权 ROE（归母扣非口径） | `fina_indicator.roe_dt` |
| PIT 可见性 | `end_date` / `ann_date` / latest-known-as-of 分层处理 | 不得只按报告期末取数 |
| 时间基准 | A 股交易日历 | 不得用自然日或 `freq="B"` 近似财报可见窗口 |

### 11.5 数据新鲜度判断（A 股适配）

基于 A 股财报披露实际日期判断新鲜度：

| 最新报告期 | 法定披露截止 | 正常窗口 | 过期阈值 | stale 阈值 |
|-----------|:--------:|---------|---------|-----------|
| Q1 季报 (3/31) | 4/30 | ≤ 5/30 | > 90 天 | > 150 天 |
| Q2 半年报 (6/30) | 8/31 | ≤ 9/30 | > 90 天 | > 150 天 |
| Q3 季报 (9/30) | 10/31 | ≤ 11/30 | > 90 天 | > 150 天 |
| Q4 年报 (12/31) | 次年 4/30 | ≤ 次年 5/30 | > 90 天 | > 180 天 |

**实际判断逻辑：** 取 `fina_pit_ext.actual_date`（实际披露日），距今 > 90 天触发 flag #1，> 180 天触发 flag #2。PIT 语义要求不基于 `end_date`（报告期截止日），而基于 `actual_date`（实际可获取日）。

**一致性要求：** 若同一 `ts_code + end_date` 存在多次修订披露，运行时必须按 `ann_date DESC` 做 latest-known-as-of 选择，再做去重；不得把 `end_date` 相同但 `ann_date` 更晚的修订版本误当作未来信息或直接覆盖历史可见版本。

### 11.6 Adapter 实现约束

1. **不暴露底层实现细节**：Adapter 返回统一的 dataclass/DataFrame，不返回 SQLAlchemy Row 或天软 OPI 原始响应
2. **不硬编码连接信息**：AlphaDB 使用 `~/.alphahome/config.json`，tinydata 使用环境变量 `TINYDATA_USER` / `TINYDATA_PASSWORD`
3. **不打印敏感信息**：不暴露数据库 URL、密码、API token
4. **错误统一映射**：底层异常映射为 `DataSourceError` / `DataSourceTimeoutError` / `DataSourceUnavailableError`
5. **PIT 语义透传**：`as_of_date` 参数必须透传到底层数据源的 PIT 机制（AlphaDB `fina_pit_ext`，tinydata `as_of_date` 参数）
6. **缓存策略**：tinydata 自带本地 parquet 缓存（`~/.tinydata/cache/`），AlphaDB 为本地 PG 无需额外缓存

### 11.7 Fallback 策略

| 场景 | 主数据源 | Fallback | 对 AnalysisCard 的影响 |
|------|---------|---------|---------------------|
| 历史财务数据不可用 | AlphaDB | tinydata（历史 API） | 二者均不可用 → domain_status=unavailable |
| 日行情滞后 > 3 日 | AlphaDB | tinydata（实时行情） | tinydata 补齐最新交易日 |
| 估值数据不可用 | AlphaDB `stock_dailybasic` | 从 tinydata 组合计算 | 组合计算不可用 → valuation 指标 = null |
| 行业对标完全不可用 | AlphaDB SQL 聚合 | — | industry_median = null，peer 字段 unknown |
| 历史估值序列 < 3 年 | AlphaDB `stock_dailybasic` | — | confidence *= 0.75，不阻断 |
| tinydata 实时行情不可用 | tinydata | AlphaDB（T+1 延迟后可接受） | 非实时场景无影响 |

### 11.8 Mock 策略（A 股适配）

MVP 阶段允许 mock 数据源（JSON/parquet fixture files），但必须：
- 使用真实 A 股公司 ts_code（如 `000001.SZ` 平安银行、`600519.SH` 贵州茅台、`603986.SH` 兆易创新）
- 遵循 CAS 会计准则的字段名和数据结构
- 包含至少 8 个季度历史（满足 TTM + 3y CAGR 计算）
- Mock fixture 的 DataFrame schema 必须与 Adapter 返回的 StandardContract schema 一致

---

## 11A. Data Source Adapter Architecture

> **架构说明**：Adapter 接口和实现属于独立的 `crosslens_adapters` 基础设施包，不专属于 Fundamentals 域。所有能力域（Fundamentals、Technical、Macro/Meso、Sentiment、Event Driven）共享同一套 Adapter。

### 11A.1 设计原则

Fundamentals 域不直接依赖 AlphaDB 或 tinydata 的实现细节。所有数据获取通过统一的 Adapter 接口完成。

```text
crosslens_adapters/              # 独立基础设施包
  base.py                        # CrossLensDataAdapter Protocol
  registry.py                    # AdapterRegistry
  alphadb.py                     # AlphaDB 实现
  tinydata_adapter.py            # TinyData 实现
  mock.py                        # MockAdapter

crosslens_fundamentals/          # 域逻辑
  pipeline.py                    # from crosslens_adapters import CrossLensDataAdapter
    ↓ 调用
DataAdapter Interface (abstract Protocol)
    ├── AlphaDBAdapter    — 离线主力（历史 + 批量）
    └── TinyDataAdapter   — 实时补充（PIT + 最新）
    ↓ 实现
AlphaDB PostgreSQL / tinydata TS-OPI HTTP
```

### 11A.2 项目依赖关系

```text
crosslens-core/
  src/
    crosslens_adapters/          # 独立包
      __init__.py
      base.py                    # CrossLensDataAdapter Protocol + StandardContract
      registry.py                # AdapterRegistry
      alphadb.py
      tinydata_adapter.py
      mock.py

    crosslens_fundamentals/      # 域逻辑
      __init__.py
      metrics/
      classifiers/
      pipeline.py                # from crosslens_adapters import CrossLensDataAdapter
      card.py
      validation.py
      stance.py
      confidence.py
      templates.py
```

CrossLens 通过标准 Python import 引用 `crosslens_adapters` 包：
- `from crosslens_adapters import CrossLensDataAdapter, create_default_registry`
- `from crosslens_adapters.alphadb import AlphaDBAdapter`

`crosslens_adapters` 包独立维护，可被所有能力域共享。底层连接：
- AlphaDB：SQLAlchemy + `~/.alphahome/config.json`（无需 alphahome Python 包）
- tinydata：天软 TS-OPI HTTP（`E:\CodePrograms\tinydata`）

### 11A.3 Adapter Protocol 定义（伪代码）

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
import pandas as pd


class DataSourceError(Exception):
    """底层数据源不可恢复错误。"""
    def __init__(self, source: str, detail: str): ...

class DataSourceUnavailableError(DataSourceError):
    """数据源暂时不可用（网络、认证、超时）。"""


@dataclass
class FinancialStatements:
    """财务报表聚合结果。"""
    income: pd.DataFrame          # 利润表 DataFrame
    balance_sheet: pd.DataFrame   # 资产负债表 DataFrame
    cash_flow: pd.DataFrame       # 现金流量表 DataFrame
    source: str                   # "alphadb" | "tinydata" | "mock"
    as_of_date: str | None        # PIT 截止日期


@dataclass
class FinancialIndicators:
    """综合财务指标。"""
    indicators: pd.DataFrame      # fina_indicator DataFrame
    source: str


@dataclass
class MarketData:
    """行情 + 估值聚合结果。"""
    daily: pd.DataFrame           # 日线行情 DataFrame
    valuation: pd.DataFrame       # 每日估值 DataFrame
    source: str


@runtime_checkable
class CrossLensDataAdapter(Protocol):
    """CrossLens 统一数据源适配器接口（跨域共享）。

    所有实现类必须完成底层 schema → StandardContract 映射。
    返回的 DataFrame 列名为 StandardContract 规范名（见 §3.2 各 Evidence 类型定义）。
    """

    @property
    def source_name(self) -> str:
        """数据源标识：'alphadb' | 'tinydata' | 'mock'."""
        ...

    def get_financial_statements(
        self,
        ts_code: str,
        report_periods: list[str],
        *,
        as_of_date: str | None = None,
    ) -> FinancialStatements:
        """获取利润表 + 资产负债表 + 现金流量表。

        Args:
            ts_code: 股票代码（如 000001.SZ、600519.SH）
            report_periods: 报告期列表（如 ['20251231', '20250930']）
            as_of_date: PIT 截止日期（可选），仅返回该日期前已披露的数据

        Returns:
            FinancialStatements，包含 3 张表的 DataFrame

        Raises:
            DataSourceUnavailableError: 数据源不可用
            ValueError: 参数错误
        """
        ...

    def get_financial_indicators(
        self,
        ts_code: str,
        report_periods: list[str],
    ) -> FinancialIndicators:
        """获取综合财务指标（ROE、ROIC、毛利率等）。"""
        ...

    def get_market_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> MarketData:
        """获取日线行情 + 每日估值数据。"""
        ...

    def get_historical_valuation_sequence(
        self,
        ts_code: str,
        years: int = 5,
    ) -> pd.DataFrame:
        """获取 N 年历史估值序列（PE/PB/EV-EBITDA 日线）。"""
        ...

    def get_industry_peers(
        self,
        ts_code: str,
        trade_date: str,
    ) -> list[str]:
        """获取同行业公司的 ts_code 列表（申万行业分类）。"""
        ...

    def get_trade_calendar(
        self,
        start_date: str,
        end_date: str,
    ) -> list[str]:
        """获取 A 股交易日列表。"""
        ...

    def get_disclosure_dates(
        self,
        ts_code: str,
        report_periods: list[str],
    ) -> dict[str, str]:
        """获取各报告期的实际披露日期。PIT 语义。"""
        ...

    def is_available(self) -> bool:
        """数据源是否可用（网络 + 认证检查）。"""
        ...


class AlphaDBAdapter:
    """AlphaDB 适配器实现。
    
    底层：PostgreSQL（`E:\CodePrograms\alphaHome`）
    认证：`~/.alphahome/config.json`
    访问：`alphahome.providers.AlphaDataTool` 或直接 SQL
    """
    ...


class TinyDataAdapter:
    """tinydata 适配器实现。
    
    底层：天软 TS-OPI HTTP API（`E:\CodePrograms\tinydata`）
    认证：环境变量 `TINYDATA_USER` / `TINYDATA_PASSWORD`
    访问：`import tinydata as td`
    缓存：`~/.tinydata/cache/`（本地 parquet）
    """
    ...


class MockAdapter:
    """Mock 适配器（测试用）。
    
    从 JSON/parquet fixture 文件读取，返回与真实 Adapter 一致的 dataclass。
    用于 §5 管线的单元测试和集成测试。
    """
    ...
```

### 11A.4 Adapter 与 StandardContract 的映射关系

| StandardContract 字段 | AlphaDB 来源列 | tinydata 来源列 | 说明 |
|---|---|---|---|
| `operating_revenue` | `fina_income.operating_revenue` | `td.fina_income()` → `operating_revenue` | 营业收入 |
| `net_profit_parent` | `fina_income.net_profit_parent` | `td.fina_income()` → `net_profit_parent` | 归母净利润 |
| `total_assets` | `fina_balancesheet.total_assets` | `td.fina_balancesheet()` → `total_assets` | 总资产 |
| `total_equity` | `fina_balancesheet.total_equity` | `td.fina_balancesheet()` → `total_equity` | 所有者权益 |
| `operating_cashflow` | `fina_cashflow.n_cashflow_act` | `td.fina_cashflow()` → `n_cashflow_act` | 经营活动现金流净额 |
| `capex` | `fina_cashflow.c_cap_ex` | `td.fina_cashflow()` → `c_cap_ex` | 资本开支 |
| `roe` | `fina_indicator.roe_dt` | `td.fina_indicator()` → `roe_dt` | 加权 ROE（扣非） |
| `gross_profit_margin` | `fina_indicator.grossprofit_margin` | `td.fina_indicator()` → `grossprofit_margin` | 毛利率 |
| `pe_ttm` | `stock_dailybasic.pe_ttm` | 需组合计算 | PE(TTM) |
| `total_mv` | `stock_dailybasic.total_mv` | 需组合计算 | 总市值（万元） |
| `industry_sw` | `stock_industry_versioned.industry_sw` | `td.stock_industry_versioned()` | 申万行业 |
| `actual_disclosure_date` | `fina_pit_ext.actual_date` | `td.fina_indicator(as_of_date=...)` 的可用性 | 实际披露日 |

> **说明：** 上表是 SPEC-013 v0.2.0 新增的 StandardContract 映射表。StandardContract 是 Adapter 返回的列名规范，独立于底层 AlphaDB/tinydata 的实际列名。如果 AlphaDB/tinydata 将来升级 schema，只需修改 Adapter 实现，不影响 Fundamentals 域核心代码。

### 11A.5 Adapter 实现注意事项

1. **不在此 SPEC 中实现 Adapter 代码**：§11A 定义的是接口契约和伪代码，具体实现属于 `plan/tasks-fundamentals.md` 的开发任务。
2. **两个依赖包独立维护**：AlphaDB/tinydata 的 schema 可能变更，Adapter 需要做兼容处理，但不修改底层包。
3. **MockAdapter 优先实现**：在真实 Adapter 就绪前，MockAdapter 应最先完成，以便 §5 Pipeline 和 §13 Testability 的单元测试可以先行。

---

## 12. MVP Scope

### MVP 交付

1. ✅ 完整的 computed Evidence 计算管线（13 个 metrics，§4）
2. ✅ 结构化质量分类（7 个 domain_payload 枚举，§3+§7）
3. ✅ Analysis Card 生成（含所有必填字段，§9）
4. ✅ constraint_exports 正确导出（13 个，§4）
5. ✅ 域级验证（8 项检查，§10）
6. ✅ stance 判断（加权打分，§7）
7. ✅ confidence 聚合（加权平均 + cap，§8）
8. ✅ 确定性部分可单元测试（§13）

### MVP 不交付（明确排除）

1. ❌ 完整 LLM summary 生成（可用模板占位）
2. ❌ 实时数据推送（MVP 用批量拉取 / mock fixtures）
3. ❌ 多市场适配（MVP 仅支持 A 股市场，中国会计准则 CAS，申万行业分类 SWHY）
4. ❌ 历史回测验证（Pipeline 正确性只靠单元测试 + fixture 集成测试）
5. ❌ 自动数据源切换（fallback 策略为手动配置）
6. ❌ DuPont 分解详细分析（ROE 只计算总体，不分解）
7. ❌ DCF 估值模型（MVP 只用历史分位法）

### Mock 策略

- MVP 阶段允许 mock 数据源（JSON/parquet fixture files）
- Mock 数据必须使用真实 A 股公司 ts_code（如 000001.SZ 平安银行、600519.SH 贵州茅台、603986.SH 兆易创新）
- Mock 数据必须覆盖：
  - Happy path：全部 9 种 Evidence Packet 可用，估值适中，增长良好（如 000001.SZ 平安银行 2025 年报）
  - 降级场景 1：valuation_metrics 不可用（数据源缺失）
  - 降级场景 2：财报数据 > 180 天（数据过期）
  - 降级场景 3：负盈利（PE 无意义）+ 高杠杆（如 600519.SH 模拟负净利场景）
- Mock 数据的 schema 必须与 Adapter StandardContract schema 一致（见 §11A.4）

### 开放问题

1. **peer_comparison 数据源**：MVP 是否需要行业对标数据？若不可用，`industry_median_revenue_growth_ttm` 如何填充？
2. **growth_capex_flag 的 3y_avg 基准**：3 年平均值在数据不足 3 年时如何处理？
3. **LLM summary 的最小质量门槛**：MVP 模板占位的 summary 是否满足下游消费？
4. **金融股特殊处理**：银行/保险的杠杆指标（net_debt_to_ebitda）不适用，需要替代指标集。MVP 是否支持金融股？
5. **上游 SPEC 未覆盖**：SPEC-004 §20 的 `operating_margin_3y_avg` 在 constraint_exports 中未列出但可能被 Playbook 引用。需确认是否需要补充。
6. **data_quality → confidence_cap 映射统一化**：§8.3 的映射为 SPEC-013 自定义。需与 SPEC-004 §41 和 SPEC-009 确认是否需要全局统一的 data_quality → confidence_cap 规则。若需要，应提升为上游 SPEC 的规范性定义。

---

## 13. Testability

| 测试类型 | 覆盖范围 | 目标 | 工具 |
|---------|---------|------|------|
| 单元测试 | 每个 computed metric 公式 | 给定输入 → 确定性输出 | pytest + fixture |
| 单元测试 | 每个 structured 分类器 | 给定指标 → 正确 label | pytest |
| 单元测试 | stance 聚合算法 | 给定子信号 → 正确 stance | pytest |
| 单元测试 | confidence 聚合公式 | 给定子 confidence → 正确总 confidence | pytest |
| 集成测试 | 完整管线（mock 数据） | 给定 fixture → 正确 AnalysisCard | pytest + spec004 Pydantic 校验 |
| 边界测试 | 数据缺失 | 正确 domain_status=partial + domain_status_reason | pytest |
| 边界测试 | 数据过期 | 正确降级 + 正确 data_quality | pytest |
| 边界测试 | 负盈利 | pe_percentile=null, valuation_state 正确处理 | pytest |
| 边界测试 | 全部数据不可用 | domain_status=unavailable | pytest |
| 契约测试 | AnalysisCard 符合 spec004 Pydantic 模型 | model_validate 无错 | crosslens_spec004.models.AnalysisCard |
| 回归测试 | 不破坏 spec003/004/005/006/009 现有测试 | 全量通过 | pytest |

**MVP 测试覆盖目标：** ≥80% 确定性代码路径（computed + structured），≥60% 总体（含 interpreted 模板路径）。

---

## 14. References

- SPEC-003 v0.3.4 §6.1 Investment Task, §6.5 Evidence Packet, §8 Analysis Domain Job, §11 Playbook Constraint
- SPEC-004 v0.2.7 §4 Analysis Card Schema, §17~§22 Fundamentals Domain, §41 Validation Rules, §45 MVP Scope
- SPEC-005 v0.2 §2 Architecture Overview, §4.4 Evidence Packet confidence rules, §5 Metric Registry
- SPEC-006 v0.3.0 Playbook constraint execution semantics, AllowedAction enum
- SPEC-009 v0.1 Governance guardrails, Evaluator, confidence_cap merge
