# SPEC-004：五类分析能力域与 Analysis Card Schema

**版本：** v0.2
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4
**文档类型：** 能力域规格 / Analysis Card Schema
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

v0.2 合并 SPEC-004 v0.1 初稿与 v0.1.1 微补丁。主要收紧：

1. Fundamentals 降级规则对齐 SPEC-003 最小分析阈值；
2. Company Event / Catalyst 的 Hard Constraint 出口收紧；
3. Macro / Meso 增加 `macro_regime_vs_playbook` 冲突；
4. 各能力域 `domain_payload` 增加枚举 allowlist；
5. Conflict Detection 对 Flag Card 的处理对齐 SPEC-003；
6. Analysis Card 增加 `data_freshness`；
7. 增加跨域 `time_horizon_mismatch` 通用冲突规则；
8. 关闭 Company Event 官方公告事件标签支撑 Hard Constraint 的 MVP 开放问题。

---

## 1. 文档目标

SPEC-004 用于定义 crosslens 中五类分析能力域的职责边界、输入输出契约、Analysis Card 标准结构、领域扩展字段、质量检查规则和 MVP 实现边界。

五类分析能力域包括：

1. Macro / Meso；
2. Fundamentals；
3. Company Event / Catalyst；
4. Sentiment；
5. Technical / Market。

本 SPEC 重点回答：

1. 每个能力域负责分析什么；
2. 每个能力域不负责什么；
3. 每个能力域读取哪些输入；
4. 每个能力域如何返回 Analysis Card；
5. Analysis Card 的通用 schema 是什么；
6. 每个能力域的 domain payload 是什么；
7. 哪些字段可以支撑 Playbook Hard Constraint；
8. 哪些字段只能用于 Soft Constraint 或解释；
9. `domain_status`、`data_quality`、`confidence` 如何定义；
10. 每个能力域在 MVP 阶段的实现边界是什么。

本 SPEC 不详细定义：

1. 每个能力域内部使用的具体模型、工具或 Agent；
2. 每个指标的计算公式；
3. 每个数据源的接入细节；
4. Investment Playbook 的完整结构；
5. Metric Registry 的完整设计；
6. Decision Trace UI；
7. Guardrail / Evaluator 的完整实现。

以上内容由后续 SPEC 定义。

---

## 2. 继承自 SPEC-003 的架构约束

SPEC-004 必须继承 SPEC-003 v0.3.4 的核心架构约束。

### 2.1 能力域不是 Agent

五类分析能力域不是五个固定 Agent。

能力域是一个能力边界，可以由以下组件组合实现：

1. 数据接口；
2. 指标计算；
3. 规则模型；
4. 分类模型；
5. 检索工具；
6. LLM / Agentic Reasoning；
7. Evaluator；
8. 领域模板。

因此，SPEC-004 定义的是能力域的输入输出契约，而不是 Agent 人设。

### 2.2 能力域不得直接相互调用

MVP 阶段，能力域之间必须逻辑独立。

能力域不得：

1. 直接读取其他能力域的 Analysis Card；
2. 直接调用其他能力域；
3. 修改共享 Evidence Packet；
4. 修改 Context Bundle；
5. 通过共享状态影响其他能力域输出。

能力域只能读取：

```text
Investment Task
Context Bundle
Evidence Packets
Playbook Constraints
Run Config
```

能力域只能向编排器返回：

```text
Analysis Card
Domain Event Log
Error / Warning / Data Quality Flags
```

跨域融合只能发生在编排器控制的后处理节点中，包括：

1. Validation；
2. Conflict Detection；
3. Playbook Evaluation；
4. Resolved Decision Bounds；
5. Decision Candidate Generation。

### 2.3 Evidence before reasoning

能力域必须基于 Evidence Packets 生成 Analysis Card。

能力域不应直接基于模糊上下文自由分析。

如果能力域需要新的证据，应向编排器提出 evidence request，而不是自行绕过编排器抓取数据。

### 2.4 Hard Constraint 默认只能引用 Computed Evidence metrics

继承 SPEC-003 v0.3.4 的规则：

1. Hard Constraint 默认只能引用 `determinism_level = computed` 的 `metrics`；
2. Structured Evidence 的 metrics 若用于 Hard Constraint，必须标记为 `conditional_hard_constraint`；
3. Interpreted Evidence 默认不得作为 Hard Constraint 的唯一输入；
4. Soft Constraint 可以引用 facts、structured labels 或 interpreted findings，但必须保留 evidence refs。

---

## 3. Analysis Card 的产品定位

Analysis Card 是能力域向编排器返回的标准化分析结果。

它不是长篇报告，也不是最终投资建议。

Analysis Card 的作用是：

1. 把一个能力域的判断压缩为结构化对象；
2. 明确支持证据和反方证据；
3. 暴露风险和失效条件；
4. 标记数据质量和置信度；
5. 为 Conflict Detection 提供输入；
6. 为 Playbook Evaluation 提供依据；
7. 为 Decision Trace 提供可展示材料。

一句话：

> Analysis Card 是能力域级别的结构化投研判断单元。

---

## 4. Analysis Card 通用 Schema

### 4.1 最小 schema

```json
{
  "card_id": "card_fundamentals_001",
  "task_id": "task_001",
  "run_id": "run_001",
  "domain": "fundamentals",
  "domain_status": "completed",
  "summary": "基本面偏正面，但估值安全边际不足。",
  "stance": "moderately_positive",
  "confidence": 0.66,
  "confidence_reason": [
    "财务数据完整且来自 Computed Evidence",
    "估值指标可靠，但未来增长假设仍存在不确定性"
  ],
  "time_horizon": "6-12 months",
  "data_quality": "medium",
  "data_freshness": {
    "as_of": "2026-06-14",
    "oldest_evidence_as_of": "2026-03-31",
    "newest_evidence_as_of": "2026-06-14",
    "freshness_level": "quarterly",
    "staleness_risk": "medium",
    "valid_until": "2026-07-31"
  },
  "evidence_coverage": {
    "supporting_evidence_count": 3,
    "opposing_evidence_count": 2,
    "missing_required_evidence": []
  },
  "supporting_evidence": [
    {
      "evidence_id": "ev_financial_001",
      "evidence_type": "financial_metrics",
      "description": "收入增速高于行业中位数。",
      "determinism_level": "computed"
    }
  ],
  "opposing_evidence": [
    {
      "evidence_id": "ev_valuation_001",
      "evidence_type": "valuation_metrics",
      "description": "估值位于过去五年较高分位。",
      "determinism_level": "computed"
    }
  ],
  "key_findings": [
    "收入增长仍强于行业",
    "估值安全边际不足"
  ],
  "key_risks": [
    "估值压缩风险",
    "增长放缓风险"
  ],
  "invalidating_conditions": [
    "下季度收入增速低于行业中位数",
    "自由现金流转负"
  ],
  "constraint_exports": [
    {
      "metric_ref": "metric://revenue_growth_ttm",
      "evidence_ref": "ev_financial_001",
      "value_path": "metrics.revenue_growth_ttm",
      "determinism_level": "computed",
      "can_support_hard_constraint": true
    }
  ],
  "domain_payload": {},
  "warnings": [],
  "limitations": [],
  "created_at": "2026-06-14T10:30:00Z"
}
```

### 4.2 字段说明

| 字段 | 含义 |
|---|---|
| `card_id` | Analysis Card 唯一标识 |
| `task_id` | 对应 Investment Task |
| `run_id` | 对应本次分析运行 |
| `domain` | 能力域名称 |
| `domain_status` | 能力域执行状态 |
| `summary` | 简短结论 |
| `stance` | 能力域立场 |
| `confidence` | 能力域自评置信度 |
| `confidence_reason` | 置信度来源说明 |
| `time_horizon` | 判断适用周期 |
| `data_quality` | 数据质量 |
| `data_freshness` | 数据新鲜度与时效标记（v0.2 新增） |
| `evidence_coverage` | 证据覆盖情况 |
| `supporting_evidence` | 支持证据 |
| `opposing_evidence` | 反方证据 |
| `key_findings` | 关键发现 |
| `key_risks` | 关键风险 |
| `invalidating_conditions` | 失效条件 |
| `constraint_exports` | 可供 Playbook Constraint 引用的指标或事实 |
| `domain_payload` | 能力域专属字段 |
| `warnings` | 警告 |
| `limitations` | 局限 |
| `created_at` | 生成时间 |

### 4.3 data_freshness

> v0.2 新增字段。可选但推荐。

```json
{
  "data_freshness": {
    "as_of": "2026-06-14",
    "oldest_evidence_as_of": "2026-03-31",
    "newest_evidence_as_of": "2026-06-14",
    "freshness_level": "quarterly",
    "staleness_risk": "medium",
    "valid_until": "2026-07-31"
  }
}
```

| 字段 | 含义 |
|---|---|
| `as_of` | Analysis Card 判断所对应的整体日期 |
| `oldest_evidence_as_of` | 该 Card 引用的最旧 Evidence 日期 |
| `newest_evidence_as_of` | 该 Card 引用的最新 Evidence 日期 |
| `freshness_level` | 继承 SPEC-003 的数据新鲜度分级 |
| `staleness_risk` | 数据滞后风险 |
| `valid_until` | 该 Card 在默认情况下的有效期 |

`freshness_level` 枚举（继承 SPEC-003）：

```text
real_time
intraday
daily
quarterly
event_based
static
```

`staleness_risk` 枚举：

```text
low
medium
high
unknown
```

Playbook Evaluation 在引用 Analysis Card 或 `constraint_exports` 时，必须能够追溯其底层 Evidence Packet 的 `as_of` 时间。如果关键 Hard Constraint 引用的数据超过 Playbook 允许的 freshness window，应返回 `need_more_data` 或 `requires_human_review`。

---

## 5. domain_status

### 5.1 枚举

```text
completed
partial
insufficient_data
failed
skipped
```

### 5.2 语义

| domain_status | 含义 | 是否计入最小可用卡片阈值 |
|---|---|---|
| `completed` | 能力域正常完成分析 | 是 |
| `partial` | 部分完成，但存在数据缺口或低置信度 | 是，但需降权 |
| `insufficient_data` | 数据不足，无法形成有效分析 | 否 |
| `failed` | 能力域执行失败 | 否 |
| `skipped` | 编排器主动跳过 | 否 |

### 5.3 domain_status 与 data_quality 的关系

`domain_status` 和 `data_quality` 是正交字段。

`domain_status` 描述能力域是否完成任务。
`data_quality` 描述输入数据质量。

可能组合示例：

| domain_status | data_quality | 含义 |
|---|---|---|
| completed | high | 能力域完成，数据质量高 |
| completed | low | 能力域完成，但数据质量差 |
| partial | high | 数据质量高，但覆盖不完整 |
| insufficient_data | unavailable | 关键数据不可用 |
| skipped | unknown | 编排器主动跳过，未评估数据质量 |
| failed | unknown | 执行失败，无法判断数据质量 |

---

## 6. data_quality

### 6.1 枚举

```text
high
medium
low
unavailable
unknown
```

### 6.2 语义

| data_quality | 含义 |
|---|---|
| high | 数据源可靠、字段完整、时效性满足任务要求 |
| medium | 数据可用，但存在轻微缺失、延迟或覆盖不足 |
| low | 数据噪声高、覆盖不足、来源不稳定或置信度低 |
| unavailable | 数据不可用 |
| unknown | 系统无法判断数据质量 |

---

## 7. confidence

### 7.1 格式

Analysis Card 的 `confidence` 使用 0 到 1 的浮点数。

```text
0.0 <= confidence <= 1.0
```

### 7.2 语义

`confidence` 是能力域对自己分析结果可靠性的自评。

它不是：

1. 最终投资建议置信度；
2. Evaluator 评分；
3. 胜率预测；
4. 收益概率；
5. 模型准确率。

### 7.3 confidence 与 data_quality 的关系

`confidence` 必须受到 `data_quality` 约束。

MVP 阶段采用默认 confidence cap：

| data_quality | 默认 confidence 上限 |
|---|---|
| high | 0.85 |
| medium | 0.70 |
| low | 0.45 |
| unavailable | 0.20 |
| unknown | 0.50 |

### 7.4 confidence 与 domain_status 的关系

| domain_status | 默认 confidence 上限 |
|---|---|
| completed | 0.85 |
| partial | 0.60 |
| insufficient_data | 0.25 |
| failed | null 或 0 |
| skipped | null |

最终 `confidence` 不得高于由 `data_quality` 和 `domain_status` 共同决定的较低上限。

### 7.5 confidence_reason

每个 Analysis Card 必须给出 `confidence_reason`。

示例：

```json
{
  "confidence": 0.66,
  "confidence_reason": [
    "核心财务指标来自 Computed Evidence",
    "行业对比数据存在 1 个季度延迟",
    "估值分位可信，但增长预测存在不确定性"
  ]
}
```

---

## 8. stance

### 8.1 枚举

```text
positive
moderately_positive
neutral
mixed
moderately_negative
negative
insufficient_data
not_applicable
```

### 8.2 语义

| stance | 含义 |
|---|---|
| positive | 能力域结论明显正面 |
| moderately_positive | 偏正面，但有明显约束 |
| neutral | 中性 |
| mixed | 正反证据都明显 |
| moderately_negative | 偏负面，但非决定性 |
| negative | 明显负面 |
| insufficient_data | 数据不足 |
| not_applicable | 该能力域不适用于当前任务 |

MVP 阶段 Analysis Card 不使用 `strong_positive` 或 `strong_negative`，避免能力域层面过度表达。

---

## 9. constraint_exports

`constraint_exports` 用于告诉 Playbook Evaluation：该 Analysis Card 中哪些指标或事实可以被 Constraint 引用。

### 9.1 最小结构

```json
{
  "metric_ref": "metric://revenue_growth_ttm",
  "evidence_ref": "ev_financial_001",
  "value_path": "metrics.revenue_growth_ttm",
  "determinism_level": "computed",
  "can_support_hard_constraint": true
}
```

### 9.2 规则

1. `can_support_hard_constraint = true` 的 export 必须来自 Computed Evidence；
2. Structured Evidence 可以导出 metric，但默认 `can_support_hard_constraint = false`；
3. Interpreted Evidence 不得导出可支撑 Hard Constraint 的 metric；
4. facts 默认只能支撑 Soft Constraint；
5. 所有 export 必须保留 evidence_ref；
6. 若 evidence_ref 无法追溯，该 export 无效。

---

## 10. 五类能力域总览

| 能力域 | 核心问题 | 主要周期 | Hard Constraint 支撑能力 |
|---|---|---|---|
| Macro / Meso | 外部环境是否有利 | 月度 / 季度 / 年度 | 有限，仅 Computed macro/industry metrics |
| Fundamentals | 公司质地和估值是否支持投资 | 季度 / 年度 | 强，核心 Hard Constraint 来源 |
| Company Event / Catalyst | 是否存在重大事件或催化 | 日度 / 周度 / 季度 | 中等，仅 4 个 Computed metrics |
| Sentiment | 市场叙事和情绪是否拥挤 | 日度 / 周度 | 弱，默认不支撑 Hard Constraint |
| Technical / Market | 价格行为和市场状态是否支持行动 | 日度 / 周度 | 中等，Computed technical metrics 可支撑 |

---

# Part A：Macro / Meso Domain

## 11. Macro / Meso 能力域定义

### 11.1 职责

Macro / Meso 能力域负责分析标的所处的宏观和中观环境。

它关注：

1. 市场 regime；
2. 利率环境；
3. 流动性环境；
4. 政策环境；
5. 行业资本开支周期；
6. 行业供需格局；
7. 汇率、能源、原材料等外部变量；
8. 产业周期阶段。

### 11.2 不负责

Macro / Meso 不负责：

1. 预测宏观经济；
2. 做完整资产配置；
3. 替代宏观研究报告；
4. 给出单独买卖建议；
5. 判断公司财务质量；
6. 分析公司公告细节；
7. 解释短期价格形态。

### 11.3 MVP 范围

MVP 只实现三个上下文：

1. Market Regime Context；
2. Industry / Capex Cycle Context；
3. Rate / Liquidity / Policy Context。

MVP 不实现：

1. 复杂宏观预测；
2. 完整行业供需模型；
3. 宏观因子回归；
4. 多资产配置模型；
5. 宏观情景模拟。

---

## 12. Macro / Meso 输入

Macro / Meso 消费的 Evidence Packet 类型包括：

1. `macro_rate_metrics`；
2. `liquidity_metrics`；
3. `policy_context`；
4. `industry_cycle_metrics`；
5. `capex_cycle_metrics`；
6. `commodity_or_input_cost_metrics`；
7. `market_regime_label`；
8. `macro_event_summary`。

### 12.1 Computed Evidence 示例

```json
{
  "evidence_id": "ev_macro_rate_001",
  "domain": "macro_meso",
  "evidence_type": "macro_rate_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "policy_rate_change_6m": 0.5,
    "real_yield_change_6m": 0.3,
    "yield_curve_slope": -0.4
  }
}
```

### 12.2 Structured Evidence 示例

```json
{
  "evidence_id": "ev_industry_cycle_001",
  "domain": "macro_meso",
  "evidence_type": "industry_cycle_label",
  "generation_type": "structured",
  "determinism_level": "structured",
  "can_support_hard_constraint": false,
  "facts": [
    "industry_cycle_stage: early_recovery"
  ],
  "confidence": 0.62
}
```

---

## 13. Macro / Meso domain_payload

### 13.1 枚举约束

> v0.2 新增。所有状态标签必须使用以下枚举，不允许 Agent 自由发明。

#### market_regime

```text
risk_on
risk_off
neutral
volatile
unknown
```

#### rate_environment

```text
easing
tightening
stable
mixed
unknown
```

#### liquidity_environment

```text
expanding
contracting
neutral
mixed
unknown
```

#### policy_environment

```text
supportive
restrictive
neutral
mixed
unknown
```

#### industry_cycle_stage

```text
early_recovery
expansion
late_cycle
downturn
unknown
```

#### capex_cycle_stage

```text
underinvestment
capacity_expansion_starting
capacity_expansion_peak
oversupply
unknown
```

### 13.2 完整 payload

```json
{
  "market_regime": "risk_on",
  "rate_environment": "tightening",
  "liquidity_environment": "neutral",
  "policy_environment": "supportive",
  "industry_cycle_stage": "early_recovery",
  "capex_cycle_stage": "capacity_expansion_starting",
  "macro_tailwinds": [
    "政策支持行业投资",
    "行业资本开支周期进入早期扩张"
  ],
  "macro_headwinds": [
    "实际利率上行压制估值"
  ],
  "sensitive_variables": [
    "real_yield_change_6m",
    "policy_support_intensity",
    "industry_capacity_utilization"
  ]
}
```

---

## 14. Macro / Meso constraint_exports

Macro / Meso 可导出的 Hard Constraint 支撑项非常有限。

允许导出：

1. `metric://policy_rate_change_6m`；
2. `metric://real_yield_change_6m`；
3. `metric://industry_capacity_utilization`；
4. `metric://industry_capex_growth_yoy`；
5. `metric://commodity_input_cost_change`。

Structured labels，例如：

1. `market_regime = risk_on`；
2. `industry_cycle_stage = early_recovery`；
3. `policy_environment = supportive`；

默认不能支撑 Hard Constraint，只能作为 Soft Constraint 或 conditional_hard_constraint。

---

## 15. Macro / Meso 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| macro_vs_fundamentals | 宏观逆风但公司基本面强 | medium |
| macro_vs_valuation | 利率上行但估值仍高 | high |
| macro_vs_sentiment | 宏观转弱但市场情绪过热 | medium |
| industry_cycle_vs_company_event | 行业下行但公司有短期催化 | medium |
| macro_time_horizon_mismatch | 宏观周期偏长期，用户任务偏短期 | low |
| **macro_regime_vs_playbook** | **当前宏观 regime 与所选 Playbook 的适用环境明显不匹配** | **high** |

> v0.2 新增 `macro_regime_vs_playbook`。当前系统尚未实现完整 Playbook Applicability Evaluator。此冲突类型是 MVP 阶段对该能力缺口的显式风险标记。完整机制由 SPEC-006 或后续 Playbook Applicability 规格定义。

示例：

```text
Playbook = capital_cycle_fundamental_playbook
rate_environment = tightening
liquidity_environment = contracting
valuation_state = expensive
```

此时 Macro / Meso 不直接阻止 Decision Candidate，但必须生成 high severity conflict，并进入 Conflict Report、Resolved Decision Bounds、Decision Trace 和 Human Review 判断路径（若适用）。

---

## 16. Macro / Meso MVP 降级规则

当 Macro / Meso 数据质量不足时：

1. `domain_status = partial`；
2. `data_quality = low` 或 `unknown`；
3. 不参与 Hard Constraint；
4. 不单独触发 buy / sell；
5. 只用于背景解释和风险提示；
6. 必须进入 Decision Trace。

---

# Part B：Fundamentals Domain

## 17. Fundamentals 能力域定义

### 17.1 职责

Fundamentals 能力域负责分析公司的基本面质量、财务表现、估值状态和长期投资基础。

它关注：

1. 收入增长；
2. 毛利率和利润率；
3. 经营杠杆；
4. 自由现金流；
5. 资产负债表；
6. ROE / ROIC；
7. 资本开支；
8. 估值水平；
9. 估值分位；
10. 同业比较。

### 17.2 不负责

Fundamentals 不负责：

1. 短线交易择时；
2. 社交媒体情绪；
3. 技术形态；
4. 宏观预测；
5. 事件冲击路径的完整解释；
6. 最终买卖决策。

---

## 18. Fundamentals 输入

Fundamentals 消费的 Evidence Packet 类型包括：

1. `financial_metrics`；
2. `growth_metrics`；
3. `margin_metrics`；
4. `cashflow_metrics`；
5. `balance_sheet_metrics`；
6. `valuation_metrics`；
7. `peer_comparison_metrics`；
8. `capital_allocation_metrics`；
9. `earnings_quality_metrics`。

### 18.1 Computed Evidence 示例

```json
{
  "evidence_id": "ev_financial_001",
  "domain": "fundamentals",
  "evidence_type": "financial_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "revenue_growth_ttm": 0.18,
    "gross_margin_ttm": 0.61,
    "gross_margin_qoq_change": -0.02,
    "fcf_margin_ttm": 0.22,
    "net_debt_to_ebitda": 0.4,
    "roe_ttm": 0.28
  }
}
```

### 18.2 Valuation Evidence 示例

```json
{
  "evidence_id": "ev_valuation_001",
  "domain": "fundamentals",
  "evidence_type": "valuation_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "pe_percentile_5y": 0.83,
    "ev_ebitda_percentile_5y": 0.78,
    "fcf_yield": 0.025
  }
}
```

---

## 19. Fundamentals domain_payload

### 19.1 枚举约束

> v0.2 新增。

#### growth_quality

```text
strong
medium
weak
deteriorating
unknown
```

#### profitability_quality

```text
high
medium
low
deteriorating
unknown
```

#### cashflow_quality

```text
strong
medium
weak
negative
unknown
```

#### balance_sheet_risk

```text
low
medium
high
unknown
```

#### valuation_state

```text
cheap
reasonable
expensive
very_expensive
unknown
```

#### earnings_quality

```text
high
medium
low
unknown
```

#### capital_allocation_quality

```text
strong
medium
weak
unknown
```

### 19.2 完整 payload

```json
{
  "growth_quality": "strong",
  "profitability_quality": "high",
  "cashflow_quality": "strong",
  "balance_sheet_risk": "low",
  "valuation_state": "expensive",
  "earnings_quality": "medium",
  "capital_allocation_quality": "unknown",
  "fundamental_tailwinds": [
    "收入增速高于行业中位数",
    "自由现金流率保持较高水平"
  ],
  "fundamental_headwinds": [
    "估值位于过去五年高分位",
    "毛利率环比略有下滑"
  ],
  "must_watch_metrics": [
    "revenue_growth_ttm",
    "gross_margin_qoq_change",
    "fcf_margin_ttm",
    "pe_percentile_5y"
  ]
}
```

---

## 20. Fundamentals constraint_exports

Fundamentals 是 MVP 中最主要的 Hard Constraint 来源。

可支持 Hard Constraint 的 metrics 包括：

1. `metric://revenue_growth_ttm`；
2. `metric://industry_median_revenue_growth_ttm`；
3. `metric://gross_margin_ttm`；
4. `metric://gross_margin_qoq_change`；
5. `metric://operating_margin_ttm`；
6. `metric://fcf_margin_ttm`；
7. `metric://net_debt_to_ebitda`；
8. `metric://roe_ttm`；
9. `metric://roic_ttm`；
10. `metric://pe_percentile_5y`；
11. `metric://ev_ebitda_percentile_5y`；
12. `metric://fcf_yield`。

这些 metrics 必须来自 Computed Evidence。

---

## 21. Fundamentals 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| fundamentals_vs_valuation | 增长强但估值过高 | medium |
| fundamentals_vs_event | 基本面稳定但重大负面事件出现 | high |
| fundamentals_vs_sentiment | 基本面改善但情绪极度悲观 | medium |
| fundamentals_vs_technical | 长期基本面好但短期趋势走弱 | medium |
| fundamentals_data_gap | 财务数据缺失或滞后 | high |

---

## 22. Fundamentals MVP 降级规则

> v0.2 更新：对齐 SPEC-003 v0.3.4 §23 的规则。

Fundamentals Card 是 MVP 阶段生成完整 Decision Candidate 的必要条件。该规则与 SPEC-003 v0.3.4 §23 的最小可用 Analysis Card 阈值一致。

1. 若 Fundamentals Card `domain_status = completed`，可进入后续流程；
2. 若 Fundamentals Card `domain_status = partial`，可进入后续流程，但必须进入 Validation 与 Decision Trace；
3. 若 Fundamentals Card `domain_status = insufficient_data`，默认输出 `analysis_incomplete`；
4. 若 Fundamentals Card `domain_status = failed`，默认输出 `analysis_incomplete`；
5. 其他能力域不得替代 Fundamentals Card。

---

# Part C：Company Event / Catalyst Domain

## 23. Company Event / Catalyst 能力域定义

### 23.1 职责

Company Event / Catalyst 能力域负责识别和解释公司层面的重大事件与潜在催化。

它关注：

1. 财报发布；
2. 业绩指引变化；
3. 管理层变动；
4. 产品发布；
5. 重大订单；
6. 监管审批；
7. 诉讼和调查；
8. 并购重组；
9. 供应链中断；
10. 资本开支计划；
11. 分红和回购；
12. 信用事件。

### 23.2 不负责

Company Event / Catalyst 不负责：

1. 计算完整财务指标；
2. 判断市场整体情绪；
3. 技术分析；
4. 宏观预测；
5. 独立给出买卖建议。

---

## 24. Company Event / Catalyst 输入

可消费的 Evidence Packet 类型包括：

1. `company_event`；
2. `earnings_release_event`；
3. `guidance_change_event`；
4. `management_change_event`；
5. `product_launch_event`；
6. `regulatory_event`；
7. `litigation_event`；
8. `mna_event`；
9. `supply_chain_event`；
10. `capital_return_event`。

### 24.1 Structured Evidence 示例

```json
{
  "evidence_id": "ev_event_001",
  "domain": "company_event_catalyst",
  "evidence_type": "guidance_change_event",
  "generation_type": "structured",
  "determinism_level": "structured",
  "can_support_hard_constraint": false,
  "facts": [
    "management_guidance_raised",
    "revenue_guidance_above_consensus"
  ],
  "confidence": 0.74,
  "data_quality": "medium"
}
```

### 24.2 Computed Evidence 示例

```json
{
  "evidence_id": "ev_event_price_001",
  "domain": "company_event_catalyst",
  "evidence_type": "post_event_price_reaction",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "post_event_1d_return": 0.06,
    "post_event_volume_vs_20d_average": 2.4
  }
}
```

---

## 25. Company Event / Catalyst domain_payload

### 25.1 枚举约束

> v0.2 新增。

#### event_direction

```text
positive
negative
neutral
mixed
unknown
```

#### event_materiality

```text
high
medium
low
unknown
```

#### event_certainty

```text
confirmed
partially_confirmed
rumor
unknown
```

#### catalyst_direction

```text
positive
negative
neutral
mixed
unknown
```

#### catalyst_strength

```text
high
medium
low
unknown
```

#### catalyst_timing

```text
near_term
medium_term
long_term
unknown
```

### 25.2 完整 payload

```json
{
  "event_list": [
    {
      "event_type": "guidance_change",
      "event_direction": "positive",
      "event_materiality": "high",
      "event_certainty": "confirmed",
      "expected_time_horizon": "1-2 quarters",
      "source_evidence_ref": "ev_event_001"
    }
  ],
  "catalyst_direction": "positive",
  "catalyst_strength": "medium",
  "catalyst_timing": "near_term",
  "event_risks": [
    "市场已部分定价",
    "后续执行风险仍需观察"
  ],
  "invalidating_events": [
    "下次业绩指引重新下调",
    "监管审批延迟"
  ]
}
```

---

## 26. Company Event / Catalyst constraint_exports

> v0.2 收紧。MVP 阶段事件标签一律不支撑 Hard Constraint。

MVP 阶段，Company Event / Catalyst 的 Hard Constraint 出口仅限于 Computed Evidence metrics。

允许支撑 Hard Constraint 的字段仅包括：

```text
metric://post_event_1d_return
metric://post_event_volume_vs_20d_average
metric://days_since_event
metric://event_frequency_90d
```

以下事件标签一律不得支撑 Hard Constraint：

```text
management_guidance_raised
management_guidance_lowered
regulatory_approval_received
litigation_risk_identified
product_launch_confirmed
mna_announced
supply_chain_disruption_identified
capital_return_announced
```

这些标签只能作为：

1. Soft Constraint；
2. Event explanation；
3. Catalyst context；
4. Decision Trace 中的事实性线索；
5. Governance / Evaluator 后续检查对象。

原因：

1. 事件标签即使来自官方公告，也需要抽取、分类和解释；
2. 事件标签属于 Structured Evidence 或 Facts，不应直接作为 Hard Constraint 的唯一输入；
3. 让 Event 能力域自行判断"自己输出的事件标签是否足够可靠"，会形成循环自证；
4. 官方公告事实能否升级为 Hard Constraint，应由 SPEC-009 Governance 或 SPEC-006 Playbook 机制统一定义。

---

## 27. Company Event / Catalyst 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| event_vs_fundamentals | 短期正面催化但长期基本面弱 | medium |
| event_vs_sentiment | 事件正面但市场情绪负面 | medium |
| event_vs_technical | 催化正面但价格已过度反应 | medium |
| event_vs_guardrail | 重大事件未充分确认但系统倾向强建议 | high |
| event_certainty_gap | 事件来源不可靠或未确认 | high |

---

## 28. Company Event / Catalyst MVP 降级规则

当事件证据不足时：

1. `domain_status = partial` 或 `insufficient_data`；
2. 不得把传闻当作事实；
3. 不得将 Interpreted Evidence 作为事件发生的唯一依据；
4. 事件影响路径可以由 Agentic Reasoning 解释，但必须标记为解释性判断；
5. 低确定性事件不得支撑强建议。

---

# Part D：Sentiment Domain

## 29. Sentiment 能力域定义

### 29.1 职责

Sentiment 能力域负责分析市场对标的的情绪、叙事和拥挤程度。

它关注：

1. 新闻语气；
2. 社交媒体讨论；
3. 散户情绪；
4. 机构叙事；
5. 关注度变化；
6. 情绪过热；
7. 恐慌状态；
8. 叙事拥挤；
9. 情绪与基本面的背离；
10. 情绪与价格行为的背离。

### 29.2 不负责

Sentiment 不负责：

1. 判断公司真实价值；
2. 判断财务质量；
3. 单独触发买入或卖出；
4. 支撑 Hard Constraint；
5. 替代新闻事实核验；
6. 预测长期收益。

---

## 30. Sentiment 输入

可消费的 Evidence Packet 类型包括：

1. `news_sentiment_score`；
2. `social_sentiment_score`；
3. `discussion_volume_metrics`；
4. `narrative_cluster_label`；
5. `retail_bullish_bearish_ratio`；
6. `attention_spike_metrics`；
7. `options_sentiment_proxy`；
8. `fund_flow_sentiment_proxy`。

### 30.1 Structured Evidence 示例

```json
{
  "evidence_id": "ev_sentiment_001",
  "domain": "sentiment",
  "evidence_type": "social_sentiment_score",
  "generation_type": "structured",
  "determinism_level": "structured",
  "can_support_hard_constraint": false,
  "metrics": {
    "bullish_ratio": 0.72,
    "discussion_volume_zscore": 2.1
  },
  "facts": [
    "retail_sentiment_overheated"
  ],
  "confidence": 0.55,
  "data_quality": "low"
}
```

---

## 31. Sentiment domain_payload

### 31.1 枚举约束

> v0.2 新增。

#### sentiment_state

```text
overheated
bullish
neutral
bearish
panic
unknown
```

#### narrative_state

```text
crowded_positive
crowded_negative
fragmented
emerging
neutral
unknown
```

#### attention_state

```text
spiking
elevated
normal
declining
unknown
```

#### retail_positioning_proxy

```text
bullish
bearish
neutral
mixed
unknown
```

### 31.2 完整 payload

```json
{
  "sentiment_state": "overheated",
  "narrative_state": "crowded_positive",
  "attention_state": "spiking",
  "retail_positioning_proxy": "bullish",
  "sentiment_tailwinds": [
    "正面叙事高度集中",
    "讨论热度显著升高"
  ],
  "sentiment_headwinds": [
    "情绪过热，追高风险上升",
    "数据来源噪声较高"
  ],
  "sentiment_divergences": [
    "情绪强于基本面确认程度"
  ]
}
```

---

## 32. Sentiment constraint_exports

Sentiment 默认不导出可支撑 Hard Constraint 的字段。

以下字段可以作为 Soft Constraint 或风险提示：

1. `metric://bullish_ratio`；
2. `metric://discussion_volume_zscore`；
3. `metric://news_sentiment_score`；
4. `fact://retail_sentiment_overheated`；
5. `fact://narrative_crowded_positive`。

即使这些字段是结构化模型输出，也默认：

```json
{
  "can_support_hard_constraint": false
}
```

---

## 33. Sentiment 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| sentiment_vs_fundamentals | 情绪极热但基本面未改善 | high |
| sentiment_vs_valuation | 情绪极热且估值过高 | high |
| sentiment_vs_event | 情绪负面但公司事件正面 | medium |
| sentiment_vs_technical | 情绪过热但价格趋势仍强 | medium |
| sentiment_data_noise | 情绪数据低质量 | low |

---

## 34. Sentiment MVP 降权规则

Sentiment 在 MVP 中默认视为高噪声能力域。

当 `data_quality = low` 时：

1. `domain_status = partial`；
2. `confidence <= 0.45`；
3. 不支撑 Hard Constraint；
4. 不单独触发 buy / sell；
5. 主要用于风险提示、过热提示、叙事观察；
6. 必须在 Decision Trace 中标记降权原因。

---

# Part E：Technical / Market Domain

## 35. Technical / Market 能力域定义

### 35.1 职责

Technical / Market 能力域负责分析价格行为、成交量、趋势、动量、波动率和流动性状态。

它关注：

1. 趋势方向；
2. 动量强弱；
3. 成交量变化；
4. 波动率；
5. 流动性；
6. 均线结构；
7. 支撑阻力；
8. 突破或跌破；
9. 风险回撤；
10. 短中期交易状态。

### 35.2 不负责

Technical / Market 不负责：

1. 判断公司长期价值；
2. 判断财务质量；
3. 替代基本面分析；
4. 单独给出长期买卖建议；
5. 解释宏观或公司事件的真实影响。

---

## 36. Technical / Market 输入

可消费的 Evidence Packet 类型包括：

1. `price_trend_metrics`；
2. `momentum_metrics`；
3. `volume_metrics`；
4. `volatility_metrics`；
5. `liquidity_metrics`；
6. `moving_average_metrics`；
7. `support_resistance_metrics`；
8. `market_microstructure_metrics`。

### 36.1 Computed Evidence 示例

```json
{
  "evidence_id": "ev_technical_001",
  "domain": "technical_market",
  "evidence_type": "price_trend_metrics",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "rsi_14d": 68,
    "price_above_50d_ma": true,
    "price_above_200d_ma": true,
    "volume_vs_20d_average": 1.4,
    "atr_14d": 0.035,
    "drawdown_from_52w_high": -0.08
  }
}
```

---

## 37. Technical / Market domain_payload

### 37.1 枚举约束

> v0.2 新增。

#### trend_state

```text
uptrend
downtrend
sideways
trend_reversal
unknown
```

#### momentum_state

```text
positive
positive_but_extended
neutral
negative
negative_but_oversold
unknown
```

#### volume_state

```text
above_average
normal
below_average
abnormal_spike
unknown
```

#### volatility_state

```text
low
normal
high
extreme
unknown
```

#### liquidity_state

```text
sufficient
thin
poor
unknown
```

### 37.2 完整 payload

```json
{
  "trend_state": "uptrend",
  "momentum_state": "positive_but_extended",
  "volume_state": "above_average",
  "volatility_state": "normal",
  "liquidity_state": "sufficient",
  "key_levels": {
    "support": [120, 112],
    "resistance": [138, 145]
  },
  "technical_tailwinds": [
    "价格位于 50 日与 200 日均线之上",
    "成交量高于 20 日均值"
  ],
  "technical_headwinds": [
    "RSI 接近过热区间",
    "短期追高风险上升"
  ]
}
```

---

## 38. Technical / Market constraint_exports

Technical / Market 可导出 Computed metrics，用于部分 Hard Constraint 或风险规则。

可导出字段包括：

1. `metric://rsi_14d`；
2. `metric://price_above_50d_ma`；
3. `metric://price_above_200d_ma`；
4. `metric://volume_vs_20d_average`；
5. `metric://atr_14d`；
6. `metric://drawdown_from_52w_high`；
7. `metric://average_dollar_volume_20d`；
8. `metric://bid_ask_spread_proxy`。

但 Technical metrics 不应单独支撑长期投资买入结论。

---

## 39. Technical / Market 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| technical_vs_fundamentals | 技术趋势弱但基本面强 | medium |
| technical_vs_valuation | 技术突破但估值过高 | medium |
| technical_vs_sentiment | 技术强势但情绪过热 | medium |
| technical_vs_event | 技术走弱但事件催化正面 | medium |
| liquidity_risk | 流动性不足但系统建议交易 | high |

---

## 40. Technical / Market MVP 降级规则

当技术数据质量不足时：

1. `domain_status = insufficient_data` 或 `partial`；
2. 不支撑择时判断；
3. 不应输出趋势确认；
4. 不应影响长期基本面 Playbook 的核心判断；
5. 可以进入 Decision Trace 说明数据缺失。

---

## 41. 能力域质量检查规则

每张 Analysis Card 必须通过以下基础检查：

1. 必须包含 `card_id`、`task_id`、`run_id`、`domain`；
2. 必须包含合法 `domain_status`；
3. 必须包含合法 `data_quality`；
4. `confidence` 必须符合上限规则；
5. 若 `domain_status = completed`，必须至少有一个 supporting_evidence 或 opposing_evidence；
6. 所有 supporting_evidence 和 opposing_evidence 必须能追溯到 Evidence Packet；
7. 如果结论为 positive 或 negative，必须包含 opposing_evidence；
8. 如果 data_quality = low，必须包含 warnings；
9. 如果有 constraint_exports，必须明确 determinism_level 和 can_support_hard_constraint；
10. 不允许未引用证据的重大判断。

---

## 42. 能力域输出与 Conflict Detection 的关系

> v0.2 更新：对齐 SPEC-003 v0.3.4 §13.4。

Conflict Detection 只读取通过 Post-card Validation 的 Analysis Cards。

Conflict Detection 使用以下字段：

1. `domain`；
2. `stance`；
3. `confidence`；
4. `data_quality`；
5. `supporting_evidence`；
6. `opposing_evidence`；
7. `constraint_exports`；
8. `domain_payload` 中的关键状态；
9. `time_horizon`。

处理规则：

1. Block 级 Card 不得参与 Conflict Detection；
2. Flag 级 Card 可以参与 Conflict Detection，但必须降低可信度；
3. Note 级 Card 正常参与 Conflict Detection；
4. 被排除或降权的 Card 必须进入 Decision Trace；
5. Conflict Report 必须记录是否存在被降权输入。

示例：

```json
{
  "conflict_report_id": "conflict_002",
  "involved_card_refs": [
    "card_fundamentals_001",
    "card_sentiment_001"
  ],
  "deweighted_card_refs": [
    "card_sentiment_001"
  ],
  "deweight_reason": "Sentiment Card 被 Post-card Validation 标记为 Flag：数据来源噪声较高。"
}
```

---

## 43. 能力域输出与 Playbook Evaluation 的关系

Playbook Evaluation 主要使用：

1. `constraint_exports`；
2. `supporting_evidence`；
3. `opposing_evidence`；
4. `domain_payload`；
5. `stance`；
6. `confidence`；
7. `data_quality`；
8. `invalidating_conditions`。

Playbook Hard Constraint 默认只能引用 `constraint_exports` 中：

```json
{
  "can_support_hard_constraint": true
}
```

的字段。

Soft Constraint 可以引用 facts、stance、domain_payload 和 interpreted findings，但必须进入 Decision Trace。

---

## 44. 跨域通用冲突规则：time_horizon_mismatch

> v0.2 新增。

当两个能力域的 `time_horizon` 相差一个数量级以上，并且二者都被用于 Decision Candidate 生成时，应标记为 `low` severity conflict。

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| `time_horizon_mismatch` | 一个能力域输出 2-6 周信号，另一个输出 6-12 月判断，Playbook 目标周期为 3-6 月 | low |

示例：

```text
Fundamentals time_horizon = 6-12 months
Technical time_horizon = 2-6 weeks
Playbook horizon = 3-6 months
```

处理方式：

1. 生成 low severity Conflict Report；
2. 不改变 allowed_actions；
3. 可轻微降低 confidence_cap；
4. 必须进入 Decision Trace；
5. Decision Trace 应说明：该冲突是周期不一致，不一定是方向冲突。

例外：如果 Playbook 明确允许多周期综合判断，则 `time_horizon_mismatch` 可以降级为 Note。

---

## 45. MVP 最小实现范围

MVP 阶段每个能力域至少需要实现：

1. 输入 Evidence Packet 过滤；
2. Analysis Card 生成；
3. domain_status 判断；
4. data_quality 判断；
5. confidence 赋值；
6. supporting_evidence / opposing_evidence 引用；
7. constraint_exports 输出；
8. warnings / limitations 输出；
9. domain_payload 输出；
10. Domain Event Log。

---

## 46. 后续 SPEC 依赖

SPEC-004 依赖和影响以下文档：

1. SPEC-003：Agentic 投研工作流架构；
2. SPEC-005：Capability Package 规范；
3. SPEC-006：Investment Playbook 规范；
4. SPEC-008：Decision Trace 与 Observability；
5. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
6. SPEC-012：数据治理与用户私有数据。

---

## 47. 开放问题

1. Analysis Card confidence 是否需要统一算法，还是由各能力域自评；
2. Metric Registry 应归入 SPEC-005 还是 SPEC-006；
3. ~~Company Event 的官方公告事实能否支撑 Hard Constraint~~ — **v0.2 已关闭：不能**；
4. Sentiment 是否应在某些短线 Playbook 中提升权重；
5. Technical / Market 是否需要区分投资型技术分析与交易型技术分析；
6. Macro / Meso 是否需要单独的行业供需模型扩展文档；
7. Analysis Card 是否需要版本化 schema。

---

## 48. v0.2 总结

SPEC-004 v0.2 定义了五类分析能力域与 Analysis Card Schema。

本版本完成以下约束：

1. 能力域不是 Agent，而是能力边界；
2. 能力域之间不得直接相互调用；
3. 每个能力域只读取 Context Bundle、Evidence Packets 和 Playbook Constraints；
4. 每个能力域只向编排器返回 Analysis Card；
5. Analysis Card 是结构化投研判断单元；
6. domain_status 与 data_quality 正交；
7. confidence 是能力域自评置信度，受双重 cap 约束；
8. constraint_exports 明确哪些字段可支撑 Playbook Constraint；
9. Fundamentals 是 MVP 中最主要的 Hard Constraint 来源；
10. Sentiment 默认降权，不支撑 Hard Constraint；
11. Macro / Meso 在 MVP 中主要提供背景和风险约束；
12. Technical / Market 可支撑部分风险和择时约束，但不单独支撑长期买入；
13. Company Event / Catalyst 事件标签一律不支撑 Hard Constraint，仅 4 个 Computed metrics 可支撑；
14. 各能力域 domain_payload 使用明确枚举 allowlist；
15. Analysis Card 增加 data_freshness 字段；
16. 增加 `macro_regime_vs_playbook` 和 `time_horizon_mismatch` 冲突规则；
17. Conflict Detection 对 Flag Card 的处理对齐 SPEC-003；
18. 每个能力域输出必须可被 Validation、Conflict Detection、Playbook Evaluation 和 Decision Trace 消费。

SPEC-004 的核心设计原则是：

```text
Domain produces card.
Card exposes evidence.
Evidence supports constraints.
Constraints shape decision.
Trace preserves accountability.
```

中文表达：

```text
能力域生成卡片；
卡片暴露证据；
证据支撑约束；
约束塑造决策；
链路保留责任。
```
