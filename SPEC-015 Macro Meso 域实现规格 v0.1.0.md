# SPEC-015：Macro/Meso 域实现规格

**版本：** v0.1.0
**状态：** Draft
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.7；SPEC-005 v0.2
**实现参考：** SPEC-013 v0.2.0（消费者域 Pipeline 模式、Evidence 边界、Adapter 映射；非规范性上游）
**上游契约：**
- SPEC-003 §6.4 (domain 枚举，macro_meso)
- SPEC-003 §6.5 (Evidence Packet schema)
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-004 §11~§16 (Macro/Meso 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-004 §4 (Analysis Card 通用 Schema)
- SPEC-004 §45 (MVP 最小实现范围)
- SPEC-005 §5 (Metric Registry)
- SPEC-005 §4.4 (Evidence Packet confidence 取值规则)
- SPEC-005 §11.3 (MVP 必须注册的 Macro/Meso P0 metrics)
- SPEC-006 §30 (MVP Playbook：macro_meso 为 optional 域，minimum_status=partial)
**目标阶段：** 域实现规格 / MVP 实现前置

---

## 1. 文档目标

本 SPEC 定义 Macro/Meso 能力域**怎么做（HOW）**：如何消费上游 Evidence Packet、计算哪些 metric、如何分类为 stance、如何组装 Analysis Card。

**不修改上游 WHAT 契约。** Macro/Meso 域的定义（消费哪些 evidence、产出哪些 payload 字段、可导出哪些 constraint_exports、有哪些冲突类型）由 SPEC-004 §11~§16 定义，本 SPEC 不重新定义、不打补丁。若实现过程中发现上游契约缺口，记录在 §12 上游冲突裁决与 CR 清单，向上游 SPEC 提变更请求。

**可单测声明。** 本 SPEC 的所有确定性计算（metric 公式、stance 阈值、confidence 公式）均可脱离 LLM 独立单元测试，符合架构宪法「Deterministic first, Agentic when necessary, Traceable always」。

**消费者域定位。** Macro/Meso 与 Fundamentals 同为消费者域（SPEC-013 §3 P0 边界）：从 Context Bundle 消费 Evidence Packet，不自行抓取数据，不向共享 Evidence Pool 回流。数据抓取是 Adapter 的职责（§10）。这与 Technical/Market 域（SPEC-014，生产者域，从 OHLCV 自行计算）不同。

### 1.1 上游冲突裁决声明

调研发现 SPEC-004 / SPEC-005 / SPEC-007 / 现有 technical_market 代码之间存在 6 项契约张力（详见 §12）。本 SPEC 作为实现层必须明确裁决，裁决原则：
- **域定义源优先**：当 SPEC-004（域定义）与 SPEC-005（Registry）冲突时，遵从 SPEC-004。
- **不打补丁**：不在本 SPEC 修改上游 SPEC 内容，只在 §12 记录裁决结论 + 向上游提 CR。

---

## 2. 域目标与边界

### 2.1 负责

Macro/Meso 能力域分析标的所处的宏观和中观环境（SPEC-004 §11.1 行 773–784）：

1. 市场 regime（risk_on / risk_off / neutral / volatile）；
2. 利率环境（easing / tightening / stable / mixed）；
3. 流动性环境（expanding / contracting / neutral / mixed）；
4. 政策环境（supportive / restrictive / neutral / mixed）；
5. 行业资本开支周期（underinvestment / capacity_expansion_starting / capacity_expansion_peak / oversupply）；
6. 行业供需格局（MVP 简化，不做完整供需模型）；
7. 汇率、能源、原材料等外部变量；
8. 产业周期阶段（early_recovery / expansion / late_cycle / downturn）。

### 2.2 不负责

SPEC-004 §11.2 行 788–796：

1. 预测宏观经济；
2. 做完整资产配置；
3. 替代宏观研究报告；
4. 给出单独买卖建议；
5. 判断公司财务质量；
6. 分析公司公告细节；
7. 解释短期价格形态。

### 2.3 MVP 边界

SPEC-004 §11.3 行 800–812 + SPEC-001 §12.2 行 425–426 + SPEC-010 §4.3 行 166 三处一致：

**MVP 只实现三个上下文（Context）：**

| Context | 覆盖范围 | 产出 payload 字段 | 消费 evidence |
|---|---|---|---|
| Market Regime Context | 市场整体风险偏好状态 | `market_regime` | `market_regime_label`, `macro_event_summary` |
| Industry / Capex Cycle Context | 行业周期与资本开支阶段 | `industry_cycle_stage`, `capex_cycle_stage` | `industry_cycle_metrics`, `capex_cycle_metrics`, `commodity_or_input_cost_metrics` |
| Rate / Liquidity / Policy Context | 利率、流动性、政策环境 | `rate_environment`, `liquidity_environment`, `policy_environment` | `macro_rate_metrics`, `liquidity_metrics`, `policy_context` |

**MVP 不实现：** 复杂宏观预测、完整行业供需模型（SPEC-010 §4.3 行 166 唯一点名的排除项）、宏观因子回归、多资产配置模型、宏观情景模拟。

### 2.4 跨域边界

| 边界 | 说明 |
|---|---|
| 与 Fundamentals | Macro/Meso 提供 `industry_cycle_stage` / `capex_cycle_stage` 作为背景；Fundamentals 不得用这些 label 推断 `growth_capex_flag`（SPEC-005 §5.2 行 768–774 must_not_infer_from_macro_label 约束）。 |
| 与 Technical/Market | `market_regime` label 的归属见 §12 CR-3：SPEC-004 §13.1 归 Macro/Meso，但 technical_market 已实现导出。本 SPEC 裁决为 Macro/Meso 产出，MVP 过渡期 technical_market 可暂存。 |
| 与 Playbook | macro_meso 在 MVP Playbook 中为 optional 域，`minimum_status = partial`（SPEC-006 §30 行 1495–1496）。长期 partial 是预期行为，不阻塞 Decision Candidate（SPEC-004 §16 行 1018）。 |

### 2.5 A 股适配

A 股市场的宏观/中观适配要点：
- 利率环境以中国国债收益率（10Y / 1Y）+ DR007（银行间流动性）为主，非美债。
- 政策环境关注央行货币政策（LPR / MLF / 降准）、产业政策（行业支持/限制目录）。
- 行业周期以申万一级/二级行业分类为基准（与 fundamentals 的 `get_industry_peers` 同口径）。
- 商品/原材料成本关注对 A 股影响大的品种（铜、铝、螺纹钢、原油、动力煤）。

---

## 3. Evidence Consumption Catalog

> **P0 架构边界（对齐 SPEC-013 §3）：** Macro/Meso 是 Evidence **消费者**，不是生产者。本域从 Context Bundle 读取上游已注入的 Evidence Packet，计算/分类后产出 Analysis Card。本域不向共享 Evidence Pool 回流新 Evidence。

### 3.1 消费的 Evidence Packet 类型

SPEC-004 §12 行 818–827 列出 8 种 evidence_type。本 SPEC 补充 required/optional 标注（解决上游缺口——SPEC-004 §12 未声明必需/可选）：

| # | evidence_type | generation_type | determinism_level | can_support_hard | 来源 Context | 必需性 |
|---|---|---|---|:---:|---|---|
| 1 | `macro_rate_metrics` | computed | computed | ✅ | Rate/Liquidity/Policy | required |
| 2 | `liquidity_metrics` | computed | computed | ✅ | Rate/Liquidity/Policy | optional |
| 3 | `policy_context` | structured | structured | ❌ | Rate/Liquidity/Policy | optional |
| 4 | `industry_cycle_metrics` | computed | computed | ✅ | Industry/Capex Cycle | required |
| 5 | `capex_cycle_metrics` | computed | computed | ✅ | Industry/Capex Cycle | optional |
| 6 | `commodity_or_input_cost_metrics` | computed | computed | ✅ | Industry/Capex Cycle | optional |
| 7 | `market_regime_label` | structured | structured | ❌ | Market Regime | required |
| 8 | `macro_event_summary` | interpreted | interpreted | ❌ | Market Regime | optional |

**必需性裁决（解决上游缺口 #6）：**
- 3 个 required evidence（`macro_rate_metrics`、`industry_cycle_metrics`、`market_regime_label`），分别覆盖三个 Context 各至少一个。其余 5 个为 optional。
- 缺失 ≥2 个 required → `domain_status = unavailable`。
- 缺失 1 个 required → `domain_status = partial`（预期常态）。
- 3 个 required 全在 → 至少 `partial`；若 optional 齐备度 ≥4/5（即 ≥4 个 optional 可用）→ `completed`（少见，宏观数据常有时滞）。

### 3.2 每种 Evidence Packet 的完整定义

#### 3.2.1 macro_rate_metrics

```text
evidence_type: macro_rate_metrics
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: Adapter.get_macro_rate_data()（§10，待新增）
获取频率: 日频（利率）/ 月频（收益率曲线）
数据源映射: AlphaDB rawdata 表（待确认，见 §10 开放问题） / tinydata 宏观接口（待确认）
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|---|---|---|---|
| policy_rate | number | % | 当前政策利率（LPR 1Y 或 MLF） |
| policy_rate_change_6m | number | pp | 6 个月政策利率变动（百分点） |
| real_yield | number | % | 当前实际利率（名义利率 - CPI 同比） |
| real_yield_change_6m | number | pp | 6 个月实际利率变动 |
| yield_curve_slope | number | pp | 10Y-1Y 国债利差 |

**confidence 赋值规则：** computed 默认 1.0；数据 >90 天 ×0.85，>180 天 ×0.70。

#### 3.2.2 liquidity_metrics

```text
evidence_type: liquidity_metrics
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: Adapter.get_liquidity_data()（§10，待新增）
获取频率: 日频
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|---|---|---|---|
| dr007 | number | % | DR007 银行间质押式回购利率 |
| dr007_change_6m | number | pp | 6 个月 DR007 变动 |
| m2_growth_yoy | number | % | M2 同比增速 |
| social_financing_growth_yoy | number | % | 社融存量同比增速 |

**confidence 赋值规则：** computed 默认 1.0；数据 >30 天 ×0.90（流动性数据时效性强）。

#### 3.2.3 policy_context

```text
evidence_type: policy_context
generation_type: structured
determinism_level: structured
can_support_hard_constraint: false
数据来源: Adapter.get_policy_events()（§10，待新增）/ 结构化政策事件流
获取频率: 事件驱动
```

**labels 字段：**

| label | 取值 | 说明 |
|---|---|---|
| monetary_policy_stance | easing / neutral / tightening | 央行货币政策取向 |
| industrial_policy_direction | supportive / neutral / restrictive | 产业政策对该行业的方向 |

**confidence 赋值规则：** structured 默认 0.70；有明确政策文件支撑 0.85，推断 0.50。

#### 3.2.4 industry_cycle_metrics

```text
evidence_type: industry_cycle_metrics
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: Adapter.get_industry_cycle_data()（§10，待新增）
获取频率: 月频 / 季频
```

> **命名裁决（解决上游冲突 #1）：** SPEC-004 §12 清单（行 823）写 `industry_cycle_metrics`，§12.2 示例（行 853）写 `industry_cycle_label`。本 SPEC 统一采用 `industry_cycle_metrics`（与清单一致；`label` 是 export 形态不是 evidence_type）。

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|---|---|---|---|
| industry_capacity_utilization | number | % | 行业产能利用率 |
| industry_pmi | number | index | 行业 PMI（如有） |
| industry_inventory_to_sales | number | ratio | 行业库存销售比 |

**confidence 赋值规则：** computed 默认 1.0；数据 >90 天 ×0.85。

#### 3.2.5 capex_cycle_metrics

```text
evidence_type: capex_cycle_metrics
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: Adapter.get_industry_cycle_data()（§10，待新增）
获取频率: 季频
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|---|---|---|---|
| industry_capex_growth_yoy | number | % | 行业资本开支同比增速 |
| industry_fixed_asset_investment_yoy | number | % | 行业固定资产投资同比 |

**confidence 赋值规则：** computed 默认 1.0；数据 >120 天 ×0.85（季频数据）。

#### 3.2.6 commodity_or_input_cost_metrics

```text
evidence_type: commodity_or_input_cost_metrics
generation_type: computed
determinism_level: computed
can_support_hard_constraint: true
数据来源: Adapter.get_commodity_data()（§10，待新增）
获取频率: 日频 / 周频
```

**metrics 字段：**

| metric | 类型 | 单位 | 说明 |
|---|---|---|---|
| commodity_input_cost_change | number | % | 关键投入品成本 6 个月变动 |
| copper_price_change_6m | number | % | 铜价 6 个月变动（工业品代理） |
| oil_price_change_6m | number | % | 原油价格 6 个月变动 |

**confidence 赋值规则：** computed 默认 1.0；数据 >30 天 ×0.90。

#### 3.2.7 market_regime_label

```text
evidence_type: market_regime_label
generation_type: structured
determinism_level: structured
can_support_hard_constraint: false
数据来源: Adapter.get_market_regime_label()（§10，待新增）/ 规则化计算
获取频率: 周频
```

> **归属裁决（解决上游冲突 #3）：** SPEC-004 §13.1（行 872）+ §14（行 973）将 `market_regime` 归 Macro/Meso domain_payload + 可导出 label。现有 `crosslens_technical_market/card.py:716` 已导出 `label://market_regime`（其 `regime_metrics` 计算结果）。本 SPEC 裁决 `market_regime` 为 Macro/Meso 域产出。MVP 过渡安排见 §12 CR-3。

**labels 字段：**

| label | 取值（SPEC-004 §13.1 行 874–880） | 说明 |
|---|---|---|
| market_regime | risk_on / risk_off / neutral / volatile / unknown | 市场整体风险偏好状态 |

**confidence 赋值规则：** structured 默认 0.70；基于明确量化规则（如 Hurst + 波动率分位）0.85，纯定性 0.50。

#### 3.2.8 macro_event_summary

```text
evidence_type: macro_event_summary
generation_type: interpreted
determinism_level: interpreted
can_support_hard_constraint: false
数据来源: 宏观事件流 / LLM 解读（可选）
获取频率: 事件驱动
```

**facts 字段：** 自由文本数组，近期影响市场的宏观事件摘要（如"美联储加息 25bp"、"行业限产政策出台"）。

**confidence 赋值规则：** interpreted 默认 0.50；有权威来源 0.65。

---

## 4. Metric Catalog

SPEC-004 §14 行 965–969 + SPEC-005 §11.3 行 1751–1758 一致定义 5 个 P0 必须注册的 Macro/Meso metric。本节给出完整 Metric Registry 条目（解决上游缺口 #4——SPEC-005 §5.2 Registry 主体缺这 5 个 metric 的完整定义）。

### 4.1 Metric 汇总

| # | metric_id | 公式类型 | 单位 | can_support_hard | 来源 Evidence | Context |
|---|---|---|---|:---:|---|---|
| 1 | `policy_rate_change_6m` | 差值 | pp | ✅ | macro_rate_metrics | Rate/Liquidity/Policy |
| 2 | `real_yield_change_6m` | 差值 | pp | ✅ | macro_rate_metrics | Rate/Liquidity/Policy |
| 3 | `industry_capacity_utilization` | 直接取值 | % | ✅ | industry_cycle_metrics | Industry/Capex Cycle |
| 4 | `industry_capex_growth_yoy` | 同比 | % | ✅ | capex_cycle_metrics | Industry/Capex Cycle |
| 5 | `commodity_input_cost_change` | 变动率 | % | ✅ | commodity_or_input_cost_metrics | Industry/Capex Cycle |

### 4.2 每个 Metric 的完整定义

#### metric://policy_rate_change_6m

**公式：**
```
policy_rate_change_6m = policy_rate[t] - policy_rate[t-126]
其中 t = 最近交易日，126 ≈ 半年交易日
正值表示加息（利率上行），负值表示降息
若历史数据不足 126 日 → 降级为可用的最长窗口（≥63 日），<63 日 → null
```

**输入数据：** `macro_rate_metrics.policy_rate`，需 ≥126 个日历日历史

**Adapter 字段映射：** `Adapter.get_macro_rate_data().policy_rate`（§10，待新增）；AlphaDB 宏观利率表（待确认表名）。

**Metric Registry 条目：**
```json
{
  "metric_id": "policy_rate_change_6m",
  "display_name": "6个月政策利率变动",
  "description": "政策利率（LPR/MLF）6个月变动，正值=加息，负值=降息。反映货币政策方向。",
  "value_type": "number",
  "unit": "percentage_point",
  "metric_category": "computed",
  "source_domain": "macro_meso",
  "producing_package": "pkg_macro_metrics_v1",
  "producing_capability": "cap_macro_rate_compute",
  "evidence_type": "macro_rate_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "policy_rate_change_6m",
  "expected_export_ref": "metric://policy_rate_change_6m",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 30,
    "valid_until_rule": "next_rate_change_plus_30_days",
    "description": "政策利率日频更新，30天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "数据 > 90 天: ×0.85",
      "数据 > 180 天: ×0.70"
    ]
  },
  "tags": ["macro", "rate", "monetary_policy", "hard_constraint"]
}
```

#### metric://real_yield_change_6m

**公式：**
```
real_yield_change_6m = real_yield[t] - real_yield[t-126]
其中 real_yield = nominal_yield - cpi_yoy
正值表示实际利率上行（压制估值），负值表示下行
若 CPI 或名义利率缺失 → real_yield = null → 本 metric = null
```

**输入数据：** `macro_rate_metrics.real_yield`（已由 adapter 用名义利率 - CPI 计算），需 ≥126 日历日

**Adapter 字段映射：** `Adapter.get_macro_rate_data().real_yield`（§10，待新增）。

**Metric Registry 条目：**
```json
{
  "metric_id": "real_yield_change_6m",
  "display_name": "6个月实际利率变动",
  "description": "实际利率（名义利率-CPI）6个月变动。实际利率上行通常压制估值。",
  "value_type": "number",
  "unit": "percentage_point",
  "metric_category": "computed",
  "source_domain": "macro_meso",
  "producing_package": "pkg_macro_metrics_v1",
  "producing_capability": "cap_macro_rate_compute",
  "evidence_type": "macro_rate_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "real_yield_change_6m",
  "expected_export_ref": "metric://real_yield_change_6m",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 30,
    "valid_until_rule": "next_cpi_release_plus_30_days",
    "description": "依赖CPI月频+利率日频，30天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "CPI 数据滞后 > 45 天: ×0.85",
      "利率数据 > 30 天: ×0.90"
    ]
  },
  "tags": ["macro", "rate", "real_yield", "hard_constraint"]
}
```

#### metric://industry_capacity_utilization

**公式：**
```
industry_capacity_utilization = 直接取行业最新产能利用率
取值范围 [0, 100]，>85% 通常预示产能紧张（利好），<70% 预示过剩
若该行业无产能利用率数据 → null
```

**输入数据：** `industry_cycle_metrics.industry_capacity_utilization`，需最近 1 期

**Adapter 字段映射：** `Adapter.get_industry_cycle_data(industry_code).capacity_utilization`（§10，待新增）。

**Metric Registry 条目：**
```json
{
  "metric_id": "industry_capacity_utilization",
  "display_name": "行业产能利用率",
  "description": "标的所属行业的产能利用率。高利用率预示产能紧张，低利用率预示过剩。",
  "value_type": "number",
  "unit": "percent",
  "metric_category": "computed",
  "source_domain": "macro_meso",
  "producing_package": "pkg_industry_cycle_classifier_v1",
  "producing_capability": "cap_industry_cycle_compute",
  "evidence_type": "industry_cycle_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "industry_capacity_utilization",
  "expected_export_ref": "metric://industry_capacity_utilization",
  "freshness_requirement": {
    "update_frequency": "monthly",
    "staleness_threshold_days": 90,
    "valid_until_rule": "next_stat_release_plus_90_days",
    "description": "统计局月频发布，90天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算（统计数据）",
    "confidence_downgrade_factors": [
      "数据 > 90 天: ×0.85",
      "行业口径变更: ×0.90"
    ]
  },
  "tags": ["meso", "industry", "capacity", "hard_constraint"]
}
```

#### metric://industry_capex_growth_yoy

**公式：**
```
industry_capex_growth_yoy = (capex[t] - capex[t-4]) / capex[t-4]
其中 t 按季度，t-4 = 去年同期
正值表示行业资本开支扩张，负值表示收缩
若 capex[t-4] <= 0 或缺失 → null
```

**输入数据：** `capex_cycle_metrics.industry_capex_growth_yoy`，需 ≥4 个季度

**Adapter 字段映射：** `Adapter.get_industry_cycle_data(industry_code).capex_yoy`（§10，待新增）。

**Metric Registry 条目：**
```json
{
  "metric_id": "industry_capex_growth_yoy",
  "display_name": "行业资本开支同比",
  "description": "行业资本开支同比增速。扩张期正值，收缩期负值。反映资本周期阶段。",
  "value_type": "number",
  "unit": "percent",
  "metric_category": "computed",
  "source_domain": "macro_meso",
  "producing_package": "pkg_industry_cycle_classifier_v1",
  "producing_capability": "cap_industry_cycle_compute",
  "evidence_type": "capex_cycle_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "industry_capex_growth_yoy",
  "expected_export_ref": "metric://industry_capex_growth_yoy",
  "freshness_requirement": {
    "update_frequency": "quarterly",
    "staleness_threshold_days": 120,
    "valid_until_rule": "next_quarter_end_plus_90_days",
    "description": "季频数据，120天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "数据 > 120 天: ×0.85",
      "行业口径变更: ×0.90"
    ]
  },
  "tags": ["meso", "industry", "capex", "capital_cycle", "hard_constraint"]
}
```

#### metric://commodity_input_cost_change

**公式：**
```
commodity_input_cost_change = (cost_index[t] - cost_index[t-126]) / cost_index[t-126]
其中 cost_index = 标的行业关键投入品价格加权指数（行业映射见 §2.5）
正值表示成本上行（利空下游），负值表示下行
若关键投入品映射缺失 → 用南华工业品指数作 fallback
若历史不足 126 日 → 降级为可用的最长窗口（≥63 日），<63 日 → null
```

**输入数据：** `commodity_or_input_cost_metrics.commodity_input_cost_change`，需 ≥126 日历日

**Adapter 字段映射：** `Adapter.get_commodity_data(industry_code).input_cost_change`（§10，待新增）。

**Metric Registry 条目：**
```json
{
  "metric_id": "commodity_input_cost_change",
  "display_name": "投入品成本6个月变动",
  "description": "行业关键投入品价格6个月变动率。成本上行利空下游，下行利好。",
  "value_type": "number",
  "unit": "percent",
  "metric_category": "computed",
  "source_domain": "macro_meso",
  "producing_package": "pkg_macro_metrics_v1",
  "producing_capability": "cap_commodity_cost_compute",
  "evidence_type": "commodity_or_input_cost_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "evidence_value_path": "commodity_input_cost_change",
  "expected_export_ref": "metric://commodity_input_cost_change",
  "freshness_requirement": {
    "update_frequency": "daily",
    "staleness_threshold_days": 30,
    "valid_until_rule": "next_trading_day_plus_30_days",
    "description": "商品价格日频，30天内有效"
  },
  "confidence_metadata": {
    "determination_type": "computed_default",
    "default_confidence": 1.0,
    "confidence_cap_reason": "确定性计算",
    "confidence_downgrade_factors": [
      "投入品映射为 fallback 指数: ×0.80",
      "数据 > 30 天: ×0.90"
    ]
  },
  "tags": ["macro", "commodity", "cost", "hard_constraint"]
}
```

---

## 5. Internal Pipeline

Macro/Meso 域采用 9 步管线，与 SPEC-013 §5 同构（消费者模式：从 Evidence 过滤开始，不从 adapter 抓取开始）。数据抓取在编排层（SPEC-007）通过 Context Bundle 注入，本域只消费。

```
function run_macro_meso_domain(job: AnalysisDomainJob) -> AnalysisCard:

    // ═══ Step 1: Input Filtering (computed) ═══
    required_evidence_types = [
        "macro_rate_metrics",        // Rate/Liquidity/Policy Context
        "industry_cycle_metrics",    // Industry/Capex Cycle Context
        "market_regime_label"        // Market Regime Context
    ]
    optional_evidence_types = [
        "liquidity_metrics", "policy_context",
        "capex_cycle_metrics", "commodity_or_input_cost_metrics",
        "macro_event_summary"
    ]

    available_evidence = filter_evidence_by_domain(job.evidence_refs, domain="macro_meso")
    missing_required = required_evidence_types - types_of(available_evidence)

    if len(missing_required) >= 2:
        return unavailable_card(
            domain_status="unavailable",
            domain_status_reason="insufficient_data",
            missing_required_evidence=missing_required
        )

    // domain_status 判定（与 §3.1 必需性裁决一致）：
    //   缺 1 required → partial；3 required 全在 → 至少 partial；
    //   3 required 全在 + optional ≥4/5 → completed
    available_optional_count = count(available_evidence ∩ optional_evidence_types)
    if len(missing_required) >= 1:
        domain_status = "partial"   // 预期常态（SPEC-004 §16 行 1018）
    elif available_optional_count >= 4:
        domain_status = "completed"
    else:
        domain_status = "partial"   // required 全在但 optional 不足 → partial

    // ═══ Step 2: Deterministic Metric Computation (computed) ═══
    // 每条 metric 公式见 §4 Metric Catalog；从对应 evidence_type 的 metrics 字段提取
    computed = {
        "policy_rate_change_6m": extract_or_compute(available_evidence, "macro_rate_metrics", "policy_rate_change_6m"),
        "real_yield_change_6m": extract_or_compute(available_evidence, "macro_rate_metrics", "real_yield_change_6m"),
        "industry_capacity_utilization": extract_or_compute(available_evidence, "industry_cycle_metrics", "industry_capacity_utilization"),
        "industry_capex_growth_yoy": extract_or_compute(available_evidence, "capex_cycle_metrics", "industry_capex_growth_yoy"),
        "commodity_input_cost_change": extract_or_compute(available_evidence, "commodity_or_input_cost_metrics", "commodity_input_cost_change"),
    }

    // ═══ Step 3: Structured Classification (structured) ═══
    // 将三个 Context 的 raw metrics/labels 分类为 6 个 payload 枚举字段（§8）
    structured_labels = {
        "market_regime": classify_market_regime(available_evidence, computed),       // §6.1
        "rate_environment": classify_rate_environment(computed),                      // §6.2
        "liquidity_environment": classify_liquidity_environment(available_evidence),  // §6.2
        "policy_environment": classify_policy_environment(available_evidence),        // §6.2
        "industry_cycle_stage": classify_industry_cycle(computed),                    // §6.3
        "capex_cycle_stage": classify_capex_cycle(computed),                          // §6.3
    }

    // ═══ Step 4: Internal Results Assembly (computed) ═══
    // computed metrics + structured labels 合并到内存，不回流 Evidence Pool
    internal_results = {**computed, **structured_labels}

    // ═══ Step 5: Stance Determination (computed) ═══
    // 三个 Context 各产出一个子 stance，加权聚合（§6.4）
    stance = determine_macro_meso_stance(structured_labels)   // §6

    // ═══ Step 6: Confidence Computation (computed) ═══
    // 计算 raw confidence（§7.1-7.2），此处尚未 clamp
    confidence = compute_raw_macro_meso_confidence(available_evidence, domain_status)  // §7

    // ═══ Step 7: Analysis Card Assembly (computed) ═══
    card = build_analysis_card(
        domain="macro_meso",
        domain_status=domain_status,
        stance=stance,
        confidence=confidence,   // raw 值，Step 8 后重新 clamp
        domain_payload=build_payload(computed, structured_labels),  // §8
        constraint_exports=build_exports(computed, structured_labels),  // §8
        supporting_evidence=..., opposing_evidence=...,
        data_quality=assess_data_quality(available_evidence),
    )

    // ═══ Step 8: Domain Validation (computed) ═══
    // validation 可能降级 domain_status（如 completed→partial）或 data_quality（如 high→low）
    card = run_macro_meso_validation(card)   // §9

    // ═══ Step 8.5: Confidence Re-clamp (computed) ═══
    // 若 Step 8 降级了 domain_status/data_quality，必须用降级后的值重新 clamp confidence
    // 到 SPEC-004 dual cap（§7.3 + §7.5）。不重算会导致 card confidence 超过降级后的 cap，
    // 无法通过 AnalysisCard._confidence_cap 校验。
    card.confidence = clamp_confidence(card.confidence, card.domain_status, card.data_quality)  // §7.3

    // ═══ Step 9: Summary & Key Findings (interpreted) ═══
    card.summary = template_summary(card)          // MVP 模板
    card.key_findings = template_key_findings(card) // MVP 模板

    return card
```

### 5.1 Pipeline 步骤 generation_type 标注

| Step | generation_type | determinism_level | 实现方式 | 可单测 |
|---|---|---|---|---|
| 1 Input Filtering | computed | computed | 纯过滤 | ✅ |
| 2 Metric Computation | computed | computed | 公式（§4） | ✅ |
| 3 Structured Classification | structured | structured | 决策树（§6） | ✅ |
| 4 Results Assembly | computed | computed | 内存合并 | ✅ |
| 5 Stance Determination | computed | computed | 加权打分（§6.4） | ✅ |
| 6 Confidence (raw) | computed | computed | 三因子公式（§7.1-7.2） | ✅ |
| 7 Card Assembly | computed | computed | 字段填充 | ✅ |
| 8 Domain Validation | computed | computed | 规则检查（§9），可能降级 status/quality | ✅ |
| 8.5 Confidence Re-clamp | computed | computed | 用降级后值 clamp 到 dual cap（§7.3/7.5） | ✅ |
| 9 Summary & Key Findings | interpreted | interpreted | 模板（MVP）/ LLM（后续） | 模板✅ / LLM❌ |

---

## 6. Stance Logic

Macro/Meso 的 stance 倾向 `neutral` / `mixed`——宏观环境极少给出强方向性（不像 fundamentals 的 positive/negative）。三个 Context 各产出一个子 stance，加权聚合。

### 6.1 Market Regime Context → 子 stance

`market_regime`（SPEC-004 §13.1 行 874–880）→ 子 stance 映射：

| market_regime | 子 stance | 说明 |
|---|---|---|
| risk_on | moderately_positive | 风险偏好上行 |
| neutral | neutral | 中性 |
| volatile | mixed | 高波动，方向不明 |
| risk_off | moderately_negative | 风险偏好下行 |
| unknown | neutral（权重×0.5） | 数据不足，降权 |

### 6.2 Rate/Liquidity/Policy Context → 子 stance

`rate_environment` + `liquidity_environment` + `policy_environment` 三者综合：

```
rlp_score = 0
if rate_environment == "easing": rlp_score += 1
elif rate_environment == "tightening": rlp_score -= 1
if liquidity_environment == "expanding": rlp_score += 1
elif liquidity_environment == "contracting": rlp_score -= 1
if policy_environment == "supportive": rlp_score += 1
elif policy_environment == "restrictive": rlp_score -= 1
// rlp_score ∈ [-3, 3]

rlp_stance:
  rlp_score >= 2  → moderately_positive
  rlp_score == 1  → moderately_positive
  rlp_score == 0  → neutral
  rlp_score == -1 → moderately_negative
  rlp_score <= -2 → moderately_negative
若三者均 unknown → 子 stance = neutral（权重×0.5）
```

### 6.3 Industry/Capex Cycle Context → 子 stance

`industry_cycle_stage`（遵从 SPEC-004 §13.1 行 914–920，解决冲突 #2）+ `capex_cycle_stage`：

| industry_cycle_stage | 子 stance | 说明 |
|---|---|---|
| early_recovery | positive | 周期复苏 |
| expansion | moderately_positive | 扩张 |
| late_cycle | moderately_negative | 后期 |
| downturn | negative | 下行 |
| unknown | neutral（权重×0.5） | — |

`capex_cycle_stage` 作为确认信号（非主导）：
- `capacity_expansion_starting` + industry 子 stance 偏多 → 维持
- `oversupply` + industry 子 stance 偏多 → 降一级（产能过剩风险）

### 6.4 子 stance 聚合为整体 stance

```
weights = {
    "market_regime": 0.40,
    "rate_liquidity_policy": 0.30,
    "industry_capex_cycle": 0.30,
}
// 权重设计：Market Regime 主导（直接影响风险偏好），另两个 Context 各 0.30
// 若某子 stance 因 unknown 降权（×0.5），其权重按比例重新归一化

score = sum(sub_stance_score[s] * effective_weight[s] for s in three_contexts)
normalized = score / sum(effective_weight[s] for s in three_contexts)

stance 阈值映射（与 SPEC-013 §7.2 一致，>= 下界 < 上界）:
  normalized >= 0.6  → positive
  normalized >= 0.2  → moderately_positive
  normalized >= -0.2 → mixed
  normalized >= -0.6 → moderately_negative
  normalized < -0.6  → negative

若 ≥2 个子 stance 为 unknown（降权后） → stance = "unavailable"
```

### 6.5 不可用处理

- ≥2 个 Context 子 stance = unknown → `stance = "unavailable"`，`domain_status` 降级（completed→partial）。
- `domain_status = unavailable` 时 stance 强制 `unavailable`。
- 注意：与 Fundamentals 不同，Macro/Meso 的 `unavailable` **不阻塞** Decision Candidate（SPEC-004 §16 行 1018），只进 Decision Trace。

---

## 7. Confidence Model

三因子模型计算 raw confidence，然后**强制 clamp 到 SPEC-004 的 dual cap**（data_quality cap 与 domain_status cap 取较小值）。本域**不覆盖**上游 SPEC-004 `AnalysisCard._confidence_cap`（`spec004/models.py:299-314`）的硬约束——任何域内公式产出的 raw confidence 若超过 dual cap，实现必须 clamp，否则 card 无法通过 AnalysisCard 校验。

### 7.1 Raw 公式

```
raw_confidence = (
    evidence_confidence_avg * 0.55 +
    completeness_factor * 0.25 +
    data_freshness_factor * 0.20
) * domain_status_multiplier
```

> 权重与 SPEC-013（0.60/0.25/0.15）略有差异：Macro/Meso 的 evidence 多为 structured/interpreted（置信度低于 fundamentals 的 computed），故降低 evidence 权重、提高 freshness 权重（宏观数据时效性更重要）。此权重只影响 raw 值，最终仍受 §7.3 dual cap 约束。

### 7.2 子项定义

- **evidence_confidence_avg**：available_evidence 的 confidence 均值。computed=1.0，structured=0.70，interpreted=0.50。
- **completeness_factor** = count(available_required + available_optional) / 8（8 = 3 required + 5 optional）。与 SPEC-013 的 9 分母不同（macro_meso 共 8 类 evidence）。
- **data_freshness_factor**：以最陈旧的 required evidence 的 as_of 计算。≤30 天→1.0，≤90 天→0.80，>90 天→0.60。阈值比 fundamentals（90/180）更严，因宏观数据时效敏感。
- **domain_status_multiplier**：completed→1.0，partial→0.90（高于 SPEC-013 的 0.80，因 partial 是 Macro/Meso 预期常态，非降级信号——但此 multiplier 只作用于 raw 值，最终仍受 §7.3 的 partial cap=0.60 约束）。

### 7.3 最终截断 — SPEC-004 dual cap（不可覆盖）

实现必须对 raw_confidence 取 `min(raw_confidence, cap_by_quality, cap_by_status)`，两个 cap 表均来自 SPEC-004 `AnalysisCard._confidence_cap`（`spec004/models.py:302-314`），本域**不修改**：

**cap_by_data_quality（`models.py:302-308`）：**

| data_quality | cap |
|---|---|
| high | 0.85 |
| medium | 0.70 |
| low | 0.45 |
| unavailable | 0.20 |
| unknown | 0.50 |

**cap_by_domain_status（`models.py:309-314`）：**

| domain_status | cap |
|---|---|
| completed | 0.85 |
| partial | 0.60 |
| unavailable | 0.25 |
| error | 0.0 |

> **关键：** Macro/Meso 长期 partial + low 是预期（SPEC-004 §16 行 1018），但 partial cap=0.60 + low cap=0.45 意味着 raw_confidence 会被压到 ≤0.45。这是上游硬约束，本域不放宽。§7.2 的 partial multiplier=0.90 只是让 raw 值不那么低（避免 partial card 的 confidence 被压到 0），但最终仍由 dual cap 兜底。若实现发现 raw 值系统性地被 dual cap 压到下限，应通过提升 evidence 质量/新鲜度改善，而非放宽 cap。

### 7.4 MVP 简化

- `macro_event_summary`（interpreted）不可用时，completeness 分母 8→7。
- `policy_context` 不可用时不影响分母（optional），但 rate_liquidity_policy 子 stance 的 policy 分量降权。

### 7.5 降级后重算

若 §9 Domain Validation 在 confidence 计算后降级了 domain_status（如 completed→partial）或 data_quality（如 high→low），实现**必须用降级后的值重新 clamp** confidence。pipeline 中 Step 6（confidence）必须在 Step 8（validation 降级）之后重新执行 clamp，不能只算一次。见 §5 pipeline 的降级重算标注。

---

## 8. Card Assembly

### 8.1 domain_payload 结构

遵从 SPEC-004 §13.2 行 934–955（6 枚举字段 + 3 自由文本数组）：

| 字段 | 类型 | 值域（SPEC-004 §13.1） | 来源 |
|---|---|---|---|
| market_regime | enum | risk_on / risk_off / neutral / volatile / unknown | §6.1 分类 |
| rate_environment | enum | easing / tightening / stable / mixed / unknown | §6.2 分类 |
| liquidity_environment | enum | expanding / contracting / neutral / mixed / unknown | §6.2 分类 |
| policy_environment | enum | supportive / restrictive / neutral / mixed / unknown | §6.2 分类 |
| industry_cycle_stage | enum | early_recovery / expansion / late_cycle / downturn / unknown | §6.3 分类（遵从 SPEC-004 §13.1，解决冲突 #2） |
| capex_cycle_stage | enum | underinvestment / capacity_expansion_starting / capacity_expansion_peak / oversupply / unknown | §6.3 分类 |
| macro_tailwinds | list[str] | 自由文本 | 模板生成（§9） |
| macro_headwinds | list[str] | 自由文本 | 模板生成（§9） |
| sensitive_variables | list[str] | metric_id / 变量名 | 选取置信度最低的 2-3 个变量 |

### 8.2 constraint_exports

遵从 SPEC-004 §14 行 965–977：

**5 个 Computed metric exports（can_support_hard_constraint=true，registration_status=registered）：**
- `metric://policy_rate_change_6m`
- `metric://real_yield_change_6m`
- `metric://industry_capacity_utilization`
- `metric://industry_capex_growth_yoy`
- `metric://commodity_input_cost_change`

仅当对应 metric 非 null 时导出；null 时不导出（不导出空值 export）。

**Structured label exports（can_support_hard_constraint=false，soft-only）：**
- `label://market_regime`（值 = market_regime 枚举）
- `label://industry_cycle_stage`（值 = industry_cycle_stage 枚举）
- `label://policy_environment`（值 = policy_environment 枚举）

> **label 归属裁决（解决冲突 #3）：** `label://market_regime` 由 Macro/Meso 域产出。MVP 过渡期 technical_market 的现有 `label://market_regime` 导出（`card.py:716`）保留，待 §12 CR-3 解决后统一。

### 8.3 supporting / opposing evidence

- **supporting_evidence**：支持当前 stance 的 evidence（如 stance 偏多 + rate_environment=easing → macro_rate_metrics 进 supporting）。
- **opposing_evidence**：与 stance 方向相反的 evidence（如 stance 偏多但 commodity_input_cost_change>0 → commodity_or_input_cost_metrics 进 opposing）。

### 8.4 schema_version

`SPEC-004@0.2.7`（与 fundamentals/technical_market 一致，见 SPEC-013 §9）。

---

## 9. Domain Validation

Macro/Meso 域级检查**全部 flag 级，无 block**（与 SPEC-013 §10 一致，异于 SPEC-014 §12 的 block/note）。Macro/Meso 不阻塞 Decision Candidate（SPEC-004 §16 行 1018），发现的问题只 flag + 进 Conflict Report。

| # | 检查项 | 触发条件 | 严重度 | 处理 |
|---|---|---|---|---|
| 1 | required evidence 缺失 | 缺失 ≥1 required evidence_type | flag | warnings += "missing_required_evidence:{type}"；domain_status 维持 partial |
| 2 | 数据陈旧 | 任一 required evidence as_of > 90 天 | flag | warnings += "stale_macro_data:{days}d"；data_quality 降为 low |
| 3 | regime 与 Playbook 冲突 | market_regime/rate_environment 与 Playbook 适用环境不匹配 | flag | 生成 `macro_regime_vs_playbook` high severity conflict（SPEC-004 §15 行 990），进 Conflict Report |
| 4 | 行业 cycle 与公司 fundamentals 冲突 | industry_cycle_stage=downturn 但 fundamentals stance 偏多 | flag | 生成 `macro_vs_fundamentals` medium conflict（SPEC-004 §15 行 985） |
| 5 | completed 但 evidence 不足 | domain_status=completed 但 available_evidence < 6 | flag | 降级 completed→partial |
| 6 | 无 stance 支撑 | stance != unavailable 但所有子 stance = unknown | flag | stance → unavailable，domain_status 降级 |
| 7 | capex label 反向使用风险 | industry_cycle_stage/capex_cycle_stage 被下游用于推断公司指标 | flag | warnings += "macro_label_misuse_risk"；记录到 Decision Trace 供 SPEC-005 约束审计 |
| 8 | sensitive_variables 缺失 | domain_payload 无 sensitive_variables | note | 补默认值 ["unknown"] |

**与 SPEC-013 §10 的差异：** 检查 #3/#4 新增 macro_meso 特有的冲突生成（对应 SPEC-004 §15 的 6 种冲突类型中 MVP 优先实现的 2 种）。检查 #7 对应 SPEC-005 §5.2 行 768–774 的反向契约约束（capex label 不得被 fundamentals 推断 growth_capex_flag）。

---

## 10. Data Source Requirements

> **关键缺口：** 现有 `CrossLensDataAdapter` Protocol（`crosslens_adapters/base.py:86-233`）**没有任何宏观/中观数据接口**——无利率、收益率曲线、流动性、政策、商品、行业产能、capex 的获取方法。5 个 P0 macro metric 要求 `determinism_level=computed` + `can_support_hard_constraint=true`，必须可计算获取。
>
> **归属裁决（解决 P1 边界矛盾）：** 这些 adapter 方法属于**上游 Evidence 注入层**，不属于 Macro/Meso 域内部 fallback。编排层（SPEC-007 Context Builder）调用 adapter 抓取宏观数据、组装成 Evidence Packet 注入 Context Bundle；Macro/Meso 域只从 Context Bundle 消费已组装的 Evidence（§1/§5 消费者边界不变）。adapter 方法放在 `crosslens_adapters` 共享包（与现有 `get_financial_statements` 等并列），不由 `crosslens_macro_meso` 域包调用。若 Context Bundle 注入失败导致某 evidence 缺失，Macro/Meso 域以 `domain_status=partial` 处理（§5 Step 1），**不自行抓数补救**。

### 10.1 新增 Adapter 方法清单（归 crosslens_adapters 共享包，由 Context Builder 调用）

以下方法需添加到 `CrossLensDataAdapter` Protocol（`base.py`）并实现于 `AlphaDBAdapter` / `TinyDataAdapter` / `MockAdapter`。**调用方是编排层 Context Builder，不是 Macro/Meso 域**（见上方归属裁决）：

| 方法 | 返回 | 覆盖 Context | 支撑 evidence_type |
|---|---|---|---|
| `get_macro_rate_data(start_date, end_date)` | `MacroRateData`（policy_rate, nominal_yield_10y, nominal_yield_1y, cpi_yoy） | Rate/Liquidity/Policy | macro_rate_metrics |
| `get_liquidity_data(start_date, end_date)` | `LiquidityData`（dr007, m2_yoy, social_financing_yoy） | Rate/Liquidity/Policy | liquidity_metrics |
| `get_policy_events(start_date, end_date)` | `list[PolicyEvent]`（type, direction, date, summary） | Rate/Liquidity/Policy | policy_context |
| `get_industry_cycle_data(industry_code, start_date, end_date)` | `IndustryCycleData`（capacity_utilization, pmi, inventory_to_sales, capex_yoy, fixed_asset_investment_yoy） | Industry/Capex Cycle | industry_cycle_metrics + capex_cycle_metrics |
| `get_commodity_data(industry_code, start_date, end_date)` | `CommodityData`（input_cost_index, copper, oil, coal） | Industry/Capex Cycle | commodity_or_input_cost_metrics |
| `get_market_regime_label(as_of_date)` | `str`（risk_on/risk_off/neutral/volatile/unknown） | Market Regime | market_regime_label |

新增 dataclass：`MacroRateData`、`LiquidityData`、`PolicyEvent`、`IndustryCycleData`、`CommodityData`（放 `base.py`，与现有 `FinancialStatements` 等并列）。

### 10.2 StandardContract 映射（基于 AlphaDB live schema 实测）

> 以下表名/字段经 AlphaDB live schema 实测确认（2026-06-20 查询 `information_schema`）。不存在 `cb_lpr`/`cb_mlf`/`cb_yield_curve`/`dr007`/`industry_capacity`/`industry_capex`/`commodity_index` 等占位表——初稿有误，已修正。

| StandardContract 字段 | AlphaDB 实际表 | AlphaDB 字段 | 单位 | 说明 / 缺口 |
|---|---|---|---|---|
| nominal_yield_10y | `rawdata.macro_yieldcurve` | `yield`（`curve_name`/`curve_term` 筛选 10Y 国债） | % | ✅ 可用 |
| nominal_yield_1y | `rawdata.macro_yieldcurve` | `yield`（`curve_term`=1Y） | % | ✅ 可用 |
| cpi_yoy | `rawdata.macro_cpi` | `nt_yoy`（全国 CPI 同比） | % | ✅ 可用 |
| m2_yoy | `rawdata.macro_cn_m` | `m2_yoy` | % | ✅ 可用 |
| social_financing_yoy | `rawdata.macro_sf_month` | `inc_cumval`（社融增量累计）/ 需算存量同比 | % | ⚠️ 表有但字段需确认存量口径 |
| dr007 | `rawdata.macro_shibor` | `1w`/`2w`（Shibor 近似，非 DR007） | % | ⚠️ **DR007 缺口**：AlphaDB 无 DR007 专表，Shibor-1W 作近似替代（口径不同，需在 evidence confidence 降权） |
| policy_rate (LPR) | — | — | % | ❌ **LPR 缺口**：AlphaDB 无 LPR/MLF 表。替代：从 `macro_yieldcurve` 政策利率曲线取，或 `macro_bond_rate` 同业存单近似。MVP 可降级为 null |
| industry_pmi | `rawdata.macro_pmi` | `pmi010000`（综合 PMI） | index | ✅ 可用（非分行业） |
| capacity_utilization | — | — | % | ❌ **产能利用率缺口**：AlphaDB 无分行业产能利用率表。MVP 该 metric = null，industry_cycle_metrics 降级 |
| capex_yoy | — | — | % | ❌ **capex 缺口**：AlphaDB 无分行业 capex 表。替代：`index_swdaily`（申万行业指数 pe/close）作行业景气代理，非直接 capex。MVP 该 metric = null 或降级代理 |
| input_cost_index | `rawdata.future_daily`（期货日线） | `close`（铜/油/煤期货合约） | index | ⚠️ 用期货价格自建投入品指数，需行业→期货品种映射 |
| oil_price | `rawdata.future_daily` | `close`（原油期货 `ts_code`） | index | ✅ 可用 |
| copper_price | `rawdata.future_daily` | `close`（铜期货 `ts_code`） | index | ✅ 可用 |

**缺口汇总（影响 §14 开放问题）：**
- **DR007**：无专表，Shibor-1W 近似（口径差异，confidence 降权）。
- **LPR/MLF**：无表，政策利率 metric 可能降级为 null（影响 `policy_rate_change_6m`）。
- **分行业产能利用率**：无表，`industry_capacity_utilization` metric MVP = null。
- **分行业 capex**：无表，`industry_capex_growth_yoy` metric MVP = null 或用申万行业指数代理。
- **商品成本指数**：无现成指数表，需用 `future_daily` 期货合约自建。

> tinydata 对宏观数据的支持范围仍待确认（§14 开放问题 #2），可能补充 LPR/DR007 实时数据。

### 10.3 数据源选择策略

```text
function select_adapter(domain="macro_meso"):
    if AlphaDBAdapter.is_available() and AlphaDB has macro tables:
        return AlphaDBAdapter   // 离线主力
    elif TinyDataAdapter.is_available() and tinydata has macro API:
        return TinyDataAdapter  // 实时补充
    else:
        return MockAdapter      // 测试/MVP 降级
```

### 10.4 Mock 策略（A 股适配）

Mock adapter 需提供宏观 fixture（JSON），覆盖三个 Context：
- `macro_rate_metrics`：policy_rate=3.45, yield_10y=2.65, cpi_yoy=0.7, real_yield≈1.95
- `liquidity_metrics`：dr007=1.85, m2_yoy=8.5, social_financing_yoy=9.0
- `industry_cycle_metrics`：capacity_utilization=78.5, pmi=50.2
- `capex_cycle_metrics`：capex_yoy=12.3, fixed_asset_investment_yoy=8.0
- `commodity_or_input_cost_metrics`：input_cost_change=3.2, copper_change=5.1, oil_change=-2.0
- `market_regime_label`：market_regime=risk_on
- `policy_context`：monetary_policy_stance=easing, industrial_policy_direction=supportive
- `macro_event_summary`：["央行降准 50bp", "行业限产政策延续"]

fixture 命名约定：`{industry_code}_macro_{scenario}.json`（如 `sw801_macro_happy.json`）。

### 10.5 数据新鲜度判断

| evidence_type | 更新频率 | stale 阈值 |
|---|---|---|
| macro_rate_metrics | 日频 | 30 天 |
| liquidity_metrics | 日频 | 30 天 |
| industry_cycle_metrics | 月频 | 90 天 |
| capex_cycle_metrics | 季频 | 120 天 |
| commodity_or_input_cost_metrics | 日频 | 30 天 |
| market_regime_label | 周频 | 14 天 |
| policy_context | 事件驱动 | 无（事件永不过期，但权重随时间衰减） |
| macro_event_summary | 事件驱动 | 无 |

---

## 11. MVP Scope

### 11.1 交付

- 三个 Context 全部实现（Market Regime / Industry-Capex Cycle / Rate-Liquidity-Policy）。
- 8 种 evidence_type 消费（3 required + 5 optional）。
- 5 个 P0 metric 计算与导出（§4）。
- 6 个 domain_payload 枚举字段分类（§6）。
- 9 步 Pipeline（§5）。
- 8 项域级 validation（§9，含 2 种冲突生成）。
- Macro/Meso Analysis Card 产出（schema_version=SPEC-004@0.2.7）。
- adapter 扩展：6 个新方法 + 5 个 dataclass（§10.1）。

### 11.2 不交付

- 复杂宏观预测模型（SPEC-004 §11.3 行 808）。
- 完整行业供需模型（SPEC-010 §4.3 行 166 唯一点名排除项）。
- 宏观因子回归（SPEC-004 §11.3 行 810）。
- 多资产配置模型（SPEC-004 §11.3 行 811）。
- 宏观情景模拟（SPEC-004 §11.3 行 812）。
- 完整 Playbook Applicability Evaluator（`macro_regime_vs_playbook` 冲突只标记，不完整裁决，SPEC-004 §15 行 992）。
- LLM 解读的 macro_event_summary（MVP 用模板/规则化事件流，§9）。

### 11.3 MVP 降级路径

| 场景 | 行为 |
|---|---|
| AlphaDB 无宏观表 | 降级 Mock fixture（§10.4），domain_status=partial |
| 行业产能利用率缺失 | industry_cycle_metrics=null，industry_cycle_stage=unknown，domain_status=partial |
| 利率数据 <63 日 | policy_rate_change_6m=null，不导出该 metric |
| market_regime_label 缺失 | market_regime=unknown，子 stance 降权，stance 倾向 neutral/mixed |
| 全部 required 缺失 | domain_status=unavailable，产出 unavailable card，进 Decision Trace 但不阻塞 Candidate |

---

## 12. 上游冲突裁决与 CR 清单

本节集中记录调研发现的 6 项上游 SPEC 之间的契约张力，及本 SPEC 的裁决结论。按 Registry 规则（SPEC-REGISTRY 行 69），实现规格不打补丁，只向上游提变更请求（CR）。

### CR-1：evidence_type 命名不一致（→ SPEC-004）

- **冲突：** SPEC-004 §12 清单（行 823）写 `industry_cycle_metrics`；§12.2 示例（行 853）写 `industry_cycle_label`。
- **裁决：** 本 SPEC 统一采用 `industry_cycle_metrics`（与清单一致；label 是 export 形态不是 evidence_type）。
- **CR：** 请 SPEC-004 修正 §12.2 示例的 `evidence_type` 为 `industry_cycle_metrics`。

### CR-2：industry_cycle_stage 枚举跨 spec 冲突（→ SPEC-005）

- **冲突：** SPEC-004 §13.1（行 914–920）= `early_recovery / expansion / late_cycle / downturn / unknown`（5 值）；SPEC-005 §5.2 Label Registry（行 976）= `early_recovery / expansion / peak / contraction / trough / unknown`（6 值）。仅 3 值重合。
- **裁决：** 本 SPEC 遵从 SPEC-004 §13.1（域定义源优先）。
- **CR：** 请 SPEC-005 §5.2 `industry_cycle_stage` 的 allowed_values 对齐 SPEC-004 §13.1 的 5 值。

### CR-3：market_regime label 归属冲突（→ SPEC-014 / technical_market 代码）

- **冲突：** SPEC-004 §13.1（行 872）+ §14（行 973）将 `market_regime` 归 Macro/Meso domain_payload + 可导出 label；但 `crosslens_technical_market/card.py:716` 已导出 `label://market_regime`（其 `regime_metrics` 计算）。
- **裁决：** `market_regime` 为 Macro/Meso 域产出（遵从 SPEC-004）。
- **MVP 过渡：** technical_market 的 `label://market_regime` 导出**暂时保留**（其 regime_metrics 已实现且通过 smoke matrix 111/0）。Macro/Meso 域实现后，由编排层（SPEC-007）决定 card 合并时以哪一方为准；过渡期两者并存，Decision Trace 记录来源。
- **CR：** 请 SPEC-014 §10.1 / §11 明确 `market_regime` 的产出方归属，并考虑 technical_market 改为引用 Macro/Meso 的 label（或保留为域内 regime_metrics 字段、不导出为 label）。

### CR-4：5 个 P0 macro metric 在 Registry 缺完整定义（→ SPEC-005）

- **冲突：** SPEC-005 §11.3（行 1751–1758）列 5 个 P0 必须注册的 macro metric，但 §5.2 Registry 主体无完整条目（`source_domain=macro_meso` 在 §5.2 仅出现于 label `industry_cycle_stage`，行 977）。`pkg_macro_metrics_v1` package 已在 §12（行 1848）预声明为 active，但产出 metric 无定义。
- **裁决：** 本 SPEC §4.2 为这 5 个 metric 补完整 Metric Registry JSON（含 producing_package/evidence_type/freshness_requirement/confidence_metadata）。
- **CR：** 请 SPEC-005 §5.2 补全这 5 个 macro metric 的 Registry 条目（可参考本 SPEC §4.2 的 JSON）。

### CR-5：domain_status 枚举跨 spec 不一致（→ SPEC-007）

- **冲突：** SPEC-004 §5.1 = `completed / partial / error / unavailable`；SPEC-007 §16.4 = `completed / partial / insufficient_data / failed / skipped`。SPEC-007 行 1926 声明"以 SPEC-004 为准"但消费 5 值中 3 个不在 SPEC-004。
- **裁决：** 本 SPEC 用 SPEC-004 枚举。macro_meso 主要落在 `partial`（两套共有值，安全）。
- **CR：** 请 SPEC-007 §16.4 的 domain_status 消费枚举对齐 SPEC-004 §5.1（或显式声明映射关系 `insufficient_data→unavailable`、`failed→error`、`skipped→unavailable`）。

### CR-6：§12 evidence 未声明 required/optional（→ SPEC-004）

- **冲突：** SPEC-004 §12（行 818–827）列 8 个 evidence_type 清单，无 required/optional 标注。
- **裁决：** 本 SPEC §3.1 自行界定必需集（3 required + 5 optional）。
- **CR：** 请 SPEC-004 §12 补 required/optional 标注（可采纳本 SPEC §3.1 的划分）。

---

## 13. Testability

| 测试类型 | 覆盖范围 | 目标 | 工具 |
|---|---|---|---|
| 单元测试 - metric 计算 | 5 个 P0 metric 公式（§4） | 边界值 + None 条件 + 降级窗口 | pytest |
| 单元测试 - 分类器 | 6 个 payload 枚举分类（§6.1–6.3） | 每个枚举值的触发条件 | pytest |
| 单元测试 - stance | 三 Context 加权聚合（§6.4） | 权重归一化 + unknown 降权 + unavailable 触发 | pytest |
| 单元测试 - confidence | 三因子公式 + cap 表（§7） | 各 data_quality cap + partial multiplier | pytest |
| 单元测试 - validation | 8 项检查（§9） | 每项触发条件 + conflict 生成 | pytest |
| 集成测试 - pipeline | 9 步端到端（§5） | Mock fixture → 完整 Card | pytest + MockAdapter |
| 契约测试 - card schema | AnalysisCard 字段（§8） | domain_payload 枚举值域 + exports 结构 | crosslens_spec004 |
| 冲突测试 | macro_regime_vs_playbook + macro_vs_fundamentals（§9 #3/#4） | conflict 生成 + 进 Conflict Report | pytest |

包结构（实现时）：`crosslens-core/src/crosslens_macro_meso/`，与 `crosslens_fundamentals` / `crosslens_technical_market` 平级。测试放 `crosslens-core/tests/test_macro_*.py`。

---

## 14. Open Questions

1. **AlphaDB 宏观表缺口（部分已实测，仍为最大风险）。** §10.2 经 live schema 实测（2026-06-20）确认：`macro_yieldcurve`/`macro_cpi`/`macro_cn_m`/`macro_sf_month`/`macro_pmi`/`macro_shibor`/`macro_bond_rate`/`future_daily`/`index_swdaily` 可用，但 **DR007、LPR/MLF、分行业产能利用率、分行业 capex 缺表**。其中 `industry_capacity_utilization` 与 `industry_capex_growth_yoy` 两个 P0 metric 无直接数据源——MVP 可能需 null 或代理降级（影响 `can_support_hard_constraint`）。若 null，5 个 P0 metric 实际只能导出 3 个。**这是 SPEC-015 进入代码实现前必须裁决的数据可得性问题。**

2. **tinydata 宏观接口范围。** tinydata 是否提供 LPR/DR007 等实时宏观数据 API？若可补充 AlphaDB 的 DR007/LPR 缺口，可避免这两个 metric 降级。

3. **行业映射口径。** `get_industry_cycle_data(industry_code)` 的 industry_code 用申万一级还是二级？需与 fundamentals 的 `get_industry_peers` 口径一致（现有用申万 SWHY）。`index_swdaily` 的 `ts_code` 需与此口径对齐。

4. **market_regime label 过渡期并存。** CR-3 的过渡安排下，Macro/Meso 与 technical_market 同时导出 `label://market_regime` 时，编排层如何合并？需 SPEC-007 明确 card 合并规则。

5. **macro_event_summary 的 LLM 边界。** MVP 用模板/规则化事件流；后续引入 LLM 解读时，如何保证 interpreted evidence 的可追溯性（架构宪法「Traceable always」）？

6. **sensitive_variables 选取算法。** §8.1 仅说"选置信度最低的 2-3 个"，具体阈值/排序算法待实现阶段确定。

7. **social_financing 存量同比口径。** `macro_sf_month` 有 `inc_cumval`（增量累计）但无现成存量同比，需确认是否自算存量或用增量近似。

---

## 15. References

- SPEC-001 §12（MVP 边界，行 425–438）
- SPEC-003 §6.4（domain 枚举）、§6.5（Evidence Packet schema）、§8（AnalysisDomainJob）
- SPEC-004 §11–§16（Macro/Meso 域定义，行 767–1018）
- SPEC-004 §4（Analysis Card 通用 Schema）
- SPEC-005 §5（Metric Registry）、§11.3（P0 macro metric 清单）
- SPEC-006 §30（MVP Playbook，macro_meso 为 optional 域）
- SPEC-007 §12.2（域调度）、§16.4（domain_status 消费）
- SPEC-010 §4.3（MVP 排除项，行 164–168）
- SPEC-013 §3–§10（消费者域 Pipeline/Evidence/Metric/Stance/Confidence/Validation 体例参考）
