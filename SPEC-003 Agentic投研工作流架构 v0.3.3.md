# SPEC-003：Agentic 投研工作流架构

**版本：** v0.3.3  
**状态：** Draft  
**项目名称：** crosslens  
**依赖文档：** SPEC-001 v0.4  
**文档类型：** 架构规格  
**目标阶段：** 产品机制设计 / MVP 架构定义  

---

## 0. 版本说明

本文件是 SPEC-003 v0.3.2 与 v0.3.3 微补丁的完整合并版。

v0.3.3 不改变 v0.3.2 的架构方向，只补齐三个规格完整性缺口：

1. Conflict escalation rules；
2. Event Log MVP schema；
3. Resolved Decision Bounds 正式 schema。

自本版本起，`SPEC-003 Agentic投研工作流架构 v0.3.3.md` 是当前唯一有效的 SPEC-003 正文。

---

## 1. 文档目标

SPEC-003 用于定义 crosslens 的 Agentic 投研工作流架构。

本 SPEC 重点回答：

1. 用户输入如何被标准化为系统任务；
2. 编排器调度的基本单元是什么；
3. 全局 Workflow 节点如何组织；
4. 编排器与五个分析能力域之间如何交互；
5. Evidence Packet、Analysis Card、Validation Report、Conflict Report、Playbook Evaluation Report、Guardrail Report、Resolved Decision Bounds、Decision Candidate、Decision Trace 如何流转；
6. Investment Playbook 在工作流中如何介入；
7. Evaluator、Guardrail、Human-in-the-loop 在哪里介入；
8. MVP 阶段的标准单股票分析流程是什么；
9. 如何避免系统在实现时滑向“LLM 生成证据、LLM 判断规则、LLM 自我审查”的不可控路径。

本 SPEC 不详细定义：

1. 五个分析能力域内部实现；
2. 每个能力域使用哪些具体模型、工具或 Agent；
3. Investment Playbook 的完整结构和管理界面；
4. Decision Trace 的完整 UI 展示方式；
5. Case Library 的结构；
6. 数据治理和用户私有数据权限。

以上内容分别由后续 SPEC 定义。

---

## 2. 架构核心判断

crosslens 不应被设计为一个“多 Agent 群聊系统”。

crosslens 的核心架构应是：

> 可控的状态化投研 Workflow，必要节点引入 Agentic Reasoning，并对全过程进行审计和复盘。

也就是说：

1. 外层：Workflow / State Machine / Orchestrator；
2. 内层：Models / Tools / Agents / Evaluators；
3. 结果：Evidence Packets + Analysis Cards + Decision Candidate + Decision Trace。

crosslens SPEC-003 的架构宪法是：

> **Deterministic first, Agentic when necessary, Traceable always.**

中文表达：

> **确定性优先；必要时才使用 Agentic 推理；全过程必须可追踪。**

---

## 3. 设计原则

### 3.1 Workflow first, Agent when needed

能用确定性流程、规则、指标、模型或工具解决的问题，不强行使用 Agent。

Agent 主要用于：开放式解释、事件影响路径分析、冲突归因、反方观点生成、不确定性表达、用户问题追问和投资语境化解释。

### 3.2 Evidence before reasoning

系统应先生成结构化 Evidence Packet，再由能力域生成 Analysis Card。

Agent 不应直接基于模糊上下文自由分析，而应基于明确证据进行解释。

### 3.3 Deterministic first

以下内容必须优先由确定性逻辑完成：

1. 技术指标计算；
2. 财务比率计算；
3. 估值分位计算；
4. 数据校验；
5. Playbook Hard Constraint 检查；
6. 最小数据阈值判断；
7. Guardrail 硬规则判断。

需要注意：Playbook Hard Constraint 的规则执行本身应是确定性的，但结果确定性取决于输入证据类型。若 Hard Constraint 引用 Structured Evidence 或 Interpreted Evidence，必须继承上游证据的不确定性，详见 Section 12。

### 3.4 编排器不侵入能力域内部实现

编排器调度全局 Workflow 节点和能力域级 Analysis Domain Job。

编排器不直接调度能力域内部的模型、工具、Agent 或子 Workflow。

能力域内部如何组合模型、工具、Workflow、Agent、Evaluator，由该能力域自行定义。

编排器只依赖能力域暴露的标准接口。

**Input**

1. Investment Task；
2. Context Bundle；
3. Evidence Packets；
4. Playbook Constraints；
5. Run Config。

**Output**

1. Analysis Card；
2. Domain Event Log；
3. Error / Warning / Data Quality Flags。

### 3.5 冲突应该被暴露，而不是被平均

如果不同能力域结论冲突，系统不应强行压成一个综合分数。

这些冲突应进入 Conflict Report，并影响 Resolved Decision Bounds 和 Decision Candidate 的建议边界。

### 3.6 用户保留最终控制权

系统可以生成投资判断候选，但不替代用户做最终投资决策。

MVP 阶段不做自动下单，不做收益承诺，不做黑箱荐股。

---

## 4. 七层架构

crosslens 的 Agentic 投研工作流采用七层职责分层：

1. User Interaction Layer；
2. Task Understanding & Routing Layer；
3. Context & Evidence Layer；
4. Orchestration Layer；
5. Execution Layer；
6. Review & Governance Layer；
7. Decision & Trace Layer。

### 4.1 七层架构是职责分层，不是严格时序

七层架构描述的是功能职责分层，而不是完整的执行时序。

Orchestration Layer 是控制平面，不是只在某个 Workflow Step 才开始执行的普通节点。

编排器从任务启动开始就负责驱动整个 Workflow，包括任务解析、Playbook 加载、Context Bundle 构建、Evidence Packet 生成、Analysis Domain Job 调度、Validation、Conflict Detection、Playbook Evaluation、Guardrail Check、Decision Candidate 生成和 Decision Trace 构建。

更准确的关系是：

> Orchestrator drives all workflow steps. Each layer owns a category of responsibilities.

中文表达：

> 编排器驱动全流程；七层架构定义职责边界；Workflow 定义执行时序。

---

## 5. 核心对象链

crosslens 标准单股票分析的核心对象链为：

```text
Investment Task
  ↓
Context Bundle
  ↓
Evidence Packets
  ↓
Analysis Domain Jobs
  ↓
Analysis Cards
  ↓
Post-card Validation Report
  ↓
Conflict Reports
  ↓
Pre-decision Validation Report
  ↓
Playbook Evaluation Report
  ↓
Guardrail Report
  ↓
Resolved Decision Bounds
  ↓
Decision Candidate
  ↓
Decision Trace
```

---

## 6. 核心对象定义

### 6.1 Investment Task

Investment Task 是系统对用户请求的标准化表达。

```json
{
  "task_id": "task_001",
  "task_type": "single_stock_buy_decision",
  "asset": {
    "symbol": "NVDA",
    "asset_type": "stock",
    "market": "US"
  },
  "user_intent": "whether_to_buy",
  "time_horizon": "3-6 months",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "depth": "standard",
  "risk_preference": "medium",
  "uses_user_private_data": true,
  "user_private_data_types": [
    "current_position",
    "historical_analysis_notes"
  ],
  "created_at": "2026-06-14T00:00:00Z"
}
```

`uses_user_private_data` 用于快速判断任务是否触及私有上下文。`user_private_data_types` 用于标记具体使用了哪些私有数据类型，并应与 SPEC-012 对齐。

### 6.2 Context Bundle

Context Bundle 是执行任务所需的上下文集合，可以包含市场行情、财务数据、公司公告、公司新闻、宏观/中观背景、社媒和情绪数据、技术指标原始数据、用户持仓、用户历史分析记录、Playbook 配置和相关历史案例。

Context Bundle 不等于最终证据。它是生成 Evidence Packet 的原材料。

### 6.3 data_quality 枚举

Context Bundle、Evidence Packet 和 Analysis Card 中的 `data_quality` 字段必须使用统一枚举。

```text
high
medium
low
unavailable
unknown
```

### 6.4 Evidence Packet

Evidence Packet 是模型、工具、检索或解释过程生成的结构化证据对象。

Evidence Packet 至少包含：

1. evidence_id；
2. task_id；
3. domain；
4. source_type；
5. source_name；
6. as_of；
7. evidence_type；
8. generation_type；
9. determinism_level；
10. can_support_hard_constraint；
11. facts 或 metrics；
12. signal；
13. confidence；
14. data_quality；
15. time_horizon；
16. limitations。

```json
{
  "evidence_id": "ev_technical_001",
  "task_id": "task_001",
  "domain": "technical_market",
  "source_type": "model_output",
  "source_name": "technical_indicator_model",
  "as_of": "2026-06-14",
  "evidence_type": "indicator_summary",
  "generation_type": "computed",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "metrics": {
    "rsi_14d": 68,
    "volume_vs_20d_average": 1.4,
    "price_above_50d_ma": true
  },
  "signal": "positive",
  "confidence": 0.72,
  "data_quality": "high",
  "time_horizon": "2-6 weeks",
  "limitations": [
    "technical signal may fail around earnings event"
  ]
}
```

### 6.5 facts 与 metrics 字段区分

Evidence Packet 可以同时支持 `metrics` 和 `facts` 字段。

`metrics` 用于结构化数值或可比较指标。

```json
{
  "metrics": {
    "revenue_growth_ttm": 0.18,
    "gross_margin_qoq_change": -0.02,
    "pe_percentile_5y": 0.83
  }
}
```

`facts` 用于文本型事实、分类标签或事件描述。

```json
{
  "facts": [
    "company_announced_capacity_expansion",
    "management_guidance_lowered",
    "sentiment_state_overheated"
  ]
}
```

Hard Constraint 默认只能引用 Computed Evidence 的 `metrics`。Soft Constraint 可以引用 `facts`，但必须保留 evidence_refs。

---

## 7. Evidence Packet 生成机制分类

Evidence Packet 不应默认由 LLM 生成。每个 Evidence Packet 必须标记其生成机制。

### 7.1 Computed Evidence

Computed Evidence 由确定性计算、规则或数据接口生成。它可复现、可测试、可审计，不依赖 LLM 推理。

示例包括财务比率、收入增速、毛利率变化、自由现金流率、估值分位、RSI、MACD、ATR、成交量放大倍数、价格相对均线位置和数据是否缺失。

### 7.2 Structured Evidence

Structured Evidence 由专门模型、分类器、规则模型或半结构化抽取器生成。

它有明确输入输出和置信度，但可能有误差，必须记录模型版本和置信度。

示例包括事件分类、情绪标签、新闻主题分类、宏观 regime 标签、行业周期阶段、风险事件识别和财报语气变化。

### 7.3 Interpreted Evidence

Interpreted Evidence 由 Agentic Reasoning 或 LLM 解释生成。

它不完全可复现，依赖上下文和模型，不应作为硬性规则的唯一依据，必须进入 Decision Trace 的不确定性说明。

```json
{
  "determinism_level": "interpreted",
  "can_support_hard_constraint": false
}
```

### 7.4 证据可靠性优先级

当不同证据冲突时，默认可靠性优先级为：

```text
Computed Evidence > Structured Evidence > Interpreted Evidence
```

但这只是证据可靠性优先级，不等于投资重要性优先级。

---

## 8. Analysis Domain Job

Analysis Domain Job 是编排器调度能力域的基本单元。

编排器不调度能力域内部节点，只提交 Analysis Domain Job。

```json
{
  "job_id": "job_fundamentals_001",
  "task_id": "task_001",
  "domain": "fundamentals",
  "input": {
    "investment_task_ref": "task_001",
    "context_bundle_ref": "ctx_001",
    "evidence_packet_refs": [
      "ev_financial_001",
      "ev_valuation_001"
    ],
    "playbook_constraints": [
      "constraint://capital_cycle_fundamental_playbook/0.1.0/growth_001"
    ]
  },
  "run_config": {
    "depth": "standard",
    "allow_agent_reasoning": true,
    "require_opposing_evidence": true
  }
}
```

`constraint://...` URI 格式是示意格式。完整 URI 规则由 SPEC-006 定义。

---

## 9. 能力域独立性约束

MVP 阶段五个能力域可以串行执行，也可以并行执行。

但无论物理执行顺序如何，能力域之间必须逻辑独立。

### 9.1 禁止行为

能力域之间不得：

1. 直接相互调用；
2. 直接读取彼此的 Analysis Card 作为输入；
3. 直接传递中间结果；
4. 修改共享 Evidence Packet；
5. 修改 Context Bundle；
6. 通过隐式状态影响其他能力域输出。

### 9.2 允许行为

能力域可以：

1. 读取同一个 Context Bundle；
2. 读取共享 Evidence Packets；
3. 使用相同的 Playbook Constraints；
4. 向编排器返回自己的 Analysis Card；
5. 在 Decision Trace 中被并列展示。

跨域信息融合只能发生在编排器控制的后处理节点中：Conflict Detection、Validation、Playbook Evaluation、Decision Bounds Resolution、Decision Candidate Generation。

### 9.3 执行隔离

实现层必须保证能力域运行时不能直接访问其他能力域的运行状态或中间输出。若使用共享内存、状态图或多 Agent 框架，应通过命名空间、状态访问权限或编排器接口限制实现隔离。

---

## 10. Analysis Card

Analysis Card 是能力域返回给编排器的标准化分析结果。

```json
{
  "card_id": "card_fundamentals_001",
  "task_id": "task_001",
  "domain": "fundamentals",
  "domain_status": "completed",
  "summary": "基本面偏正面，但估值压力较高。",
  "stance": "moderately_positive",
  "confidence": 0.66,
  "time_horizon": "6-12 months",
  "supporting_evidence": [
    {
      "evidence_id": "ev_financial_001",
      "description": "收入增速高于行业中位数。"
    }
  ],
  "opposing_evidence": [
    {
      "evidence_id": "ev_valuation_001",
      "description": "估值位于过去五年较高分位。"
    }
  ],
  "key_risks": [
    "估值压缩风险",
    "增长放缓风险"
  ],
  "invalidating_conditions": [
    "下季度收入增速低于行业中位数",
    "自由现金流转负"
  ],
  "data_quality": "medium",
  "warnings": []
}
```

### 10.1 domain_status 枚举

```text
completed
partial
insufficient_data
failed
skipped
```

| domain_status | 含义 | 下游处理 |
|---|---|---|
| completed | 能力域正常完成分析 | 可进入 Conflict Detection、Playbook Evaluation |
| partial | 能力域部分完成，但存在数据缺口或低置信度 | 可进入下游，但必须降低权重或标记警告 |
| insufficient_data | 数据不足，无法形成有效分析 | 不计入最小可用卡片阈值 |
| failed | 能力域执行失败 | 不进入 Conflict Detection，进入 Decision Trace 错误说明 |
| skipped | 编排器根据任务、Playbook 或用户设置主动跳过 | 不计入最小可用卡片阈值，但应在 Trace 中说明跳过原因 |

`skipped` 与 `insufficient_data` 的区别是：`skipped` 表示系统主动选择不运行该能力域；`insufficient_data` 表示系统尝试分析但因数据不足无法完成。

### 10.2 confidence 字段

Analysis Card 的 `confidence` MVP 阶段使用 0 到 1 的浮点数。

它是能力域自评置信度，不等于 Evaluator 评分，也不等于最终 Decision Candidate 的置信度。

Analysis Card confidence 的具体计算方式由 SPEC-004 定义。SPEC-003 仅要求它必须进入 Validation、Conflict Detection 和 Decision Trace。

---

## 11. Playbook Constraint 与 input_refs

Playbook Constraint 是 Investment Playbook 中可执行的条件对象。

```json
{
  "constraint_id": "growth_001",
  "name": "收入增速高于行业中位数",
  "condition_type": "hard",
  "input_refs": [
    "metric://revenue_growth_ttm",
    "metric://industry_median_revenue_growth_ttm"
  ],
  "operator": ">",
  "priority": "high",
  "on_fail": "block_strong_buy",
  "on_insufficient_data": "flag"
}
```

### 11.1 MVP 引用模型

MVP 阶段支持两种引用方式。

#### Evidence Value Reference

```text
evidence://{evidence_id}/{value_path}
```

示例：

```text
evidence://ev_financial_001/metrics.revenue_growth_ttm
evidence://ev_valuation_001/metrics.pe_percentile_5y
```

#### Metric Reference

```text
metric://{metric_id}
```

示例：

```text
metric://revenue_growth_ttm
metric://industry_median_revenue_growth_ttm
metric://pe_percentile_5y
```

Metric Registry 负责解析该指标来自哪个 Evidence Packet、哪个数据源和哪个时间戳。

### 11.2 引用解析要求

规则引擎执行 Hard Constraint 前，必须解析每个 `input_ref` 并获得：

1. value；
2. evidence_id；
3. source_name；
4. source_type；
5. generation_type；
6. determinism_level；
7. data_quality；
8. as_of；
9. freshness_level；
10. confidence，若适用。

如果任一必要引用无法解析，该 Constraint 状态应为 `insufficient_data`，并触发 `on_insufficient_data` 处理路径。

### 11.3 Metric Registry 的 MVP 最小形态

MVP 阶段必须提供 Metric Registry 的最小实现，用于支持 Playbook Constraint 的 `metric://` 引用。

MVP Metric Registry 可以是一个静态 JSON 映射表。

```json
{
  "metric_id": "revenue_growth_ttm",
  "display_name": "TTM 收入增速",
  "value_type": "number",
  "unit": "percent",
  "source_domain": "fundamentals",
  "preferred_evidence_type": "computed",
  "evidence_value_path": "metrics.revenue_growth_ttm",
  "freshness_requirement": "quarterly",
  "required_for_hard_constraint": true
}
```

完整 Metric Registry 设计由 SPEC-005 或 SPEC-006 定义。

---

## 12. Hard Constraint 的确定性污染风险

Hard Constraint 的执行逻辑可以是确定性的，但它所引用的输入不一定完全确定。

> A deterministic rule over uncertain evidence is not fully deterministic.

中文表达：

> 基于不确定证据执行的确定性规则，不能被视为完全确定的判断。

### 12.1 MVP 处理原则

Hard Constraint 默认只能引用 Computed Evidence 的 metrics。

如果 Hard Constraint 引用了 Structured Evidence：

1. Constraint 可以由规则引擎执行；
2. 但应标记为 `conditional_hard_constraint`；
3. 结果必须继承上游证据的不确定性；
4. `confidence` 不得默认为 1.0；
5. Decision Trace 必须标记该 Hard Constraint 的输入并非 Computed Evidence；
6. 不允许该结果单独支撑强建议。

如果 Hard Constraint 引用了 Interpreted Evidence：

1. 默认不得作为 Hard Constraint 的唯一输入；
2. 除非用户或系统显式允许；
3. 必须触发 Flag；
4. 不得支持 strong buy / strong sell。

完整的置信度传播模型由 SPEC-006 或 SPEC-009 定义。

---

## 13. Validation Report

Validation Report 是 Evaluator 对 Analysis Cards 或 Decision Candidate 前置上下文的质量检查结果。

v0.3.3 采用两阶段 Validation：

1. Post-card Validation；
2. Pre-decision Validation。

### 13.1 Post-card Validation

Post-card Validation 在 Analysis Cards 收集后立即执行。

输入：

```text
Analysis Card List
Evidence Packet List
```

主要检查：

1. Analysis Card 是否缺少必要字段；
2. 是否缺少 supporting_evidence；
3. 是否缺少 opposing_evidence；
4. evidence_refs 是否有效；
5. data_quality 是否缺失；
6. domain_status 是否有效；
7. 是否存在无证据判断；
8. 是否存在过度自信表述。

### 13.2 Pre-decision Validation

Pre-decision Validation 在 Conflict Detection 之后、Playbook Evaluation 之前执行。

输入：

```text
Analysis Cards
Conflict Reports
Post-card Validation Report
```

主要检查：

1. 是否存在未解释的高严重度冲突；
2. 模块冲突是否被充分暴露；
3. 是否达到最小 Analysis Card 阈值；
4. Fundamentals Card 是否可用；
5. 是否存在必须阻止 Decision Candidate 的 Block；
6. 是否需要人工复核；
7. 是否应将最终输出降级为 analysis_incomplete。

Pre-decision Validation 不判断 Playbook Hard Constraint 是否可执行。该判断由 Playbook Evaluation 阶段负责。

### 13.3 Validation Report 最小 schema

```json
{
  "validation_report_id": "val_post_card_001",
  "validation_stage": "post_card_validation",
  "task_id": "task_001",
  "target_type": "analysis_card_list",
  "target_refs": [
    "card_fundamentals_001",
    "card_sentiment_001"
  ],
  "findings": [
    {
      "finding_id": "finding_001",
      "severity": "flag",
      "finding_type": "missing_opposing_evidence",
      "target_ref": "card_sentiment_001",
      "description": "Sentiment Card 缺少反方证据。",
      "recommended_handling": "lower_confidence"
    }
  ],
  "overall_status": "passed_with_flags"
}
```

### 13.4 severity 与 overall_status

Finding severity：

```text
block
flag
note
```

overall_status：

```text
passed
passed_with_notes
passed_with_flags
blocked
failed
```

Post-card Validation 不直接修改 Analysis Card。Conflict Detection 在运行前必须读取 Post-card Validation Report：

1. Block 级 Card 不参与 Conflict Detection；
2. Flag 级 Card 可以参与，但降低可信度；
3. Note 级 Card 正常参与；
4. 被排除的 Card 必须进入 Decision Trace。

---

## 14. Conflict Report 与 Escalation Rules

Conflict Report 记录不同能力域之间、能力域与 Playbook 之间、或证据与结论之间的冲突。

Conflict Report 不只是展示冲突，还必须影响 Resolved Decision Bounds 和 Decision Candidate。

### 14.1 Conflict severity

```text
low
medium
high
```

### 14.2 Conflict Report 最小 schema

```json
{
  "conflict_report_id": "conflict_001",
  "task_id": "task_001",
  "conflict_type": "fundamentals_vs_valuation",
  "severity": "medium",
  "involved_domains": [
    "fundamentals",
    "technical_market"
  ],
  "involved_card_refs": [
    "card_fundamentals_001",
    "card_technical_001"
  ],
  "evidence_refs": [
    "ev_financial_001",
    "ev_valuation_001"
  ],
  "description": "基本面增长较强，但估值分位过高，二者对新开仓建议形成冲突。",
  "decision_impact": "downgrade_decision_bounds",
  "recommended_handling": "remove_buy_actions",
  "requires_human_review": false
}
```

### 14.3 severity 初始赋值规则

Conflict severity 不应完全由 LLM 判断。

MVP 阶段采用规则优先、LLM 辅助解释的方式。

#### Low conflict

满足以下任一条件时，可标记为 `low`：

1. 不涉及 Fundamentals；
2. 不涉及 Playbook Hard Constraint；
3. 冲突双方 confidence 均较低；
4. 主要基于 low quality Sentiment evidence；
5. 时间周期不一致但不影响当前任务。

默认影响：进入 Decision Trace，但不改变 allowed_actions。可轻微降低 confidence_cap。

#### Medium conflict

满足以下任一条件时，可标记为 `medium`：

1. Fundamentals 与 Technical / Sentiment 出现方向冲突；
2. Company Event 与 Sentiment 出现方向冲突；
3. Macro / Meso 与估值或行业周期判断存在冲突；
4. Playbook Soft Constraint 与某个能力域结论冲突；
5. 冲突可能影响 suggested_action，但不足以阻断分析。

默认影响：移除强建议动作，保留谨慎动作，例如 `wait`、`add_to_watchlist`、`hold_if_already_owned`。

#### High conflict

满足以下任一条件时，应标记为 `high`：

1. Fundamentals 与重大 Company Event 严重冲突；
2. Playbook Hard Constraint 与 Analysis Card 主结论冲突；
3. Guardrail 相关风险与 Decision Candidate 倾向冲突；
4. 高置信度 Computed Evidence 与高置信度能力域结论冲突；
5. 冲突足以阻止新开仓、加仓或强方向建议；
6. 多个 Medium conflict 指向同一风险方向。

默认影响：`requires_human_review = true`，并移除 `buy` / `add_position` / `strong_buy` / `strong_sell` 等强方向动作。

若冲突涉及关键 Hard Constraint，系统应输出 `analysis_incomplete` 或 `requires_human_review`。

### 14.4 多冲突聚合规则

当存在多个 Conflict Report 时，系统按最严重冲突处理。

1. 任一 High conflict → 整体 conflict impact 至少为 high；
2. 两个及以上 Medium conflict 且指向同一风险方向 → 升级为 High；
3. Medium + 多个 Low conflict → 保持 Medium，但降低 confidence_cap；
4. 仅 Low conflict → 不改变 allowed_actions，仅进入 Decision Trace；
5. Conflict Report 的影响必须进入 Resolved Decision Bounds。

### 14.5 与 Validation / Guardrail 的关系

Conflict Escalation 不覆盖 Validation Block 或 Guardrail Block。

约束优先级为：

```text
Guardrail Block
  >
Validation Block
  >
Playbook Evaluation recommended_decision_bounds
  >
Conflict escalation
  >
Soft preference / style guidance
```

---

## 15. Playbook Evaluation Report

Playbook Evaluation Report 是根据 Investment Playbook 对 Analysis Cards、Conflict Reports、Evidence Packets 进行条件检查后的结果。

它是 Decision Candidate 的直接输入之一，但不是最终建议本身。

```json
{
  "playbook_evaluation_report_id": "pbe_001",
  "task_id": "task_001",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "conditions": [
    {
      "condition_id": "ccfp_001",
      "condition_name": "行业资本开支周期有利",
      "condition_type": "soft",
      "status": "partial",
      "evidence_refs": [
        "ev_macro_001",
        "card_macro_001"
      ],
      "impact_on_decision": "caution"
    },
    {
      "condition_id": "ccfp_002",
      "condition_name": "公司财务质量未恶化",
      "condition_type": "hard",
      "status": "pass",
      "evidence_refs": [
        "card_fundamentals_001"
      ],
      "impact_on_decision": "support"
    },
    {
      "condition_id": "ccfp_003",
      "condition_name": "估值具有安全边际",
      "condition_type": "hard",
      "status": "fail",
      "evidence_refs": [
        "ev_valuation_001"
      ],
      "impact_on_decision": "block_new_position"
    }
  ],
  "blocking_conditions": [
    "估值安全边际不足"
  ],
  "overall_result": "not_passed_for_new_buy",
  "recommended_decision_bounds": [
    "wait",
    "add_to_watchlist",
    "hold_if_already_owned"
  ]
}
```

### 15.1 impact_on_decision 枚举

```text
support
neutral
caution
lower_confidence
block_strong_buy
block_strong_sell
block_new_position
block_add_position
require_human_review
need_more_data
```

### 15.2 overall_result 枚举

```text
passed
partially_passed
not_passed_for_new_buy
not_passed_for_add_position
not_suitable_for_playbook
need_more_data
requires_human_review
```

### 15.3 recommended_decision_bounds 聚合规则

MVP 阶段采用最严格约束交集规则：

1. 从默认动作集合开始；
2. 按每个 Constraint 的 `impact_on_decision` 移除不允许动作；
3. 如果任一关键 Hard Constraint 返回 `need_more_data`，则整体 `overall_result = need_more_data`；
4. 如果多数关键 Hard Constraint fail，则整体 `overall_result = not_suitable_for_playbook`；
5. 如果存在 `require_human_review`，则整体标记 `requires_human_review = true`；
6. 最终剩余动作集合写入 `recommended_decision_bounds`。

---

## 16. Guardrail Report

Guardrail Report 用于记录系统护栏规则的触发情况。

Guardrail 的目标是防止：

1. 承诺收益；
2. 无依据强买入或强卖出；
3. 数据不足时输出强方向结论；
4. 把模型预测表述为确定事实；
5. 自动下单或绕过用户确认；
6. 隐藏反方证据。

```json
{
  "guardrail_report_id": "gr_001",
  "task_id": "task_001",
  "triggered": true,
  "findings": [
    {
      "guardrail_id": "no_strong_buy_without_evidence",
      "severity": "medium",
      "description": "估值安全边际不足，不允许输出强买入建议。",
      "action": "downgrade_decision_bounds"
    }
  ],
  "overall_status": "passed_with_constraints"
}
```

### 16.1 Guardrail 优先级

Guardrail 的约束优先级高于 Playbook Evaluation 和 Conflict Escalation。

如果 Guardrail 触发 Block，则可以覆盖 Playbook Evaluation 的 `recommended_decision_bounds`。

如果 Guardrail 不是 Block，但包含 `downgrade_decision_bounds`，则应影响 Resolved Decision Bounds：

1. 从 allowed_actions 中移除强建议动作；
2. 保留谨慎动作；
3. 降低 confidence_cap；
4. 在 Decision Trace 中展示 Guardrail 降级原因。

完整 Guardrail action 语义由 SPEC-009 定义。

---

## 17. Resolved Decision Bounds

Resolved Decision Bounds 是 Decision Candidate 生成前的最终动作边界对象。

它负责合并来自以下对象的约束：

1. Validation Reports；
2. Conflict Reports；
3. Playbook Evaluation Report；
4. Guardrail Report；
5. User / Playbook preference，若适用。

Decision Candidate 只能从 Resolved Decision Bounds 的 `allowed_actions` 中选择 `suggested_action`。

### 17.1 Resolved Decision Bounds 最小 schema

```json
{
  "resolved_decision_bounds_id": "rdb_001",
  "task_id": "task_001",
  "run_id": "run_001",
  "allowed_actions": [
    "wait",
    "add_to_watchlist",
    "hold_if_already_owned"
  ],
  "blocked_actions": [
    "buy",
    "add_position",
    "strong_buy",
    "strong_sell"
  ],
  "requires_human_review": false,
  "confidence_cap": 0.62,
  "confidence_cap_reason": [
    {
      "source_type": "guardrail_report",
      "source_ref": "gr_001",
      "reason": "Sentiment 数据质量低，禁止高置信度表达。",
      "effect": "cap_confidence_at_0.62"
    }
  ],
  "source_refs": {
    "validation_report_refs": [
      "val_post_card_001",
      "val_pre_decision_001"
    ],
    "conflict_report_refs": [
      "conflict_001"
    ],
    "playbook_evaluation_report_id": "pbe_001",
    "guardrail_report_id": "gr_001"
  },
  "applied_rules": [
    {
      "rule_id": "guardrail_downgrade_low_quality_sentiment",
      "source_type": "guardrail_report",
      "effect": "remove_buy_actions"
    },
    {
      "rule_id": "medium_conflict_remove_buy_actions",
      "source_type": "conflict_report",
      "effect": "remove_buy_actions"
    }
  ],
  "reasoning": [
    "估值安全边际不足，Playbook 禁止新开仓。",
    "Sentiment 数据质量低，降低置信度。",
    "存在 medium severity 跨域冲突，移除 buy 类动作。"
  ],
  "created_at": "2026-06-14T10:35:00Z"
}
```

### 17.2 allowed_actions 枚举

MVP 支持以下动作：

```text
buy
hold
wait
avoid
reduce
add_to_watchlist
hold_if_already_owned
need_more_data
```

MVP 默认不支持：

```text
strong_buy
strong_sell
add_position
```

如果文档或实现中保留这些动作，必须进入 `blocked_actions`，除非后续 SPEC 明确支持。

### 17.3 allowed_actions 为空时的处理

如果 `allowed_actions` 为空，系统不得生成完整 Decision Candidate。

系统应输出：

```text
run_status = analysis_incomplete
```

并生成说明：

```json
{
  "message_type": "analysis_incomplete_notice",
  "suggested_next_step": "need_more_data"
}
```

该说明不应被包装为完整投资建议。

### 17.4 confidence_cap

`confidence_cap` 是 Decision Candidate 的最高置信度上限。

规则：

1. Decision Candidate 的 `confidence` 不得高于 `confidence_cap`；
2. 每一次降低 confidence_cap 必须记录在 `confidence_cap_reason`；
3. `confidence_cap` 不得由 LLM 随机生成；
4. MVP 可采用规则表赋值；
5. 完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

---

## 18. Decision Candidate

Decision Candidate 是系统生成的投资判断候选，不是最终用户决策。

```json
{
  "decision_candidate_id": "dc_001",
  "task_id": "task_001",
  "resolved_decision_bounds_id": "rdb_001",
  "playbook_evaluation_report_id": "pbe_001",
  "guardrail_report_id": "gr_001",
  "validation_report_refs": [
    "val_post_card_001",
    "val_pre_decision_001"
  ],
  "conflict_report_refs": [
    "conflict_001"
  ],
  "suggested_action": "wait",
  "confidence": 0.58,
  "action_selection_reason": "allowed_actions 中包含 wait 和 add_to_watchlist；由于估值安全边际不足且存在中等冲突，选择 wait。",
  "key_supporting_reasons": [],
  "key_opposing_reasons": [],
  "next_steps": []
}
```

Decision Candidate 的 `suggested_action` 必须满足：

```text
suggested_action ∈ allowed_actions
```

若不满足，Guardrail Checker 或 Evaluator 必须阻止输出。

---

## 19. Decision Trace

Decision Trace 是面向用户的投研证据链。

它至少回答：

1. 用户输入了什么任务；
2. 系统选择了哪条执行路径；
3. 使用了哪些数据；
4. 生成了哪些 Evidence Packets；
5. 哪些 Analysis Cards 参与判断；
6. 哪些 Validation / Conflict / Playbook / Guardrail 影响了建议边界；
7. Resolved Decision Bounds 如何形成；
8. Decision Candidate 为什么选择该 suggested_action；
9. 哪些信息缺失；
10. 哪些条件会让结论失效；
11. 用户下一步应检查什么。

Decision Trace 不应隐藏反方证据，也不应把模型预测表述为确定事实。

---

## 20. Event Log MVP Schema

Event Log 是 Observability 和 Decision Trace 的底层共享事件记录。

Decision Trace 可以选择性展示 Event Log 中与投资判断有关的事件；Observability 可以展示更完整的系统运行事件。

### 20.1 Event Log 最小 schema

```json
{
  "event_id": "evt_001",
  "run_id": "run_001",
  "task_id": "task_001",
  "timestamp": "2026-06-14T10:30:00Z",
  "event_type": "node_completed",
  "node_id": "generate_evidence_packets",
  "node_type": "workflow_node",
  "input_refs": [
    "ctx_001"
  ],
  "output_refs": [
    "ev_financial_001",
    "ev_technical_001"
  ],
  "status": "success",
  "duration_ms": 1240,
  "error": null,
  "warnings": [],
  "metadata": {
    "executor": "orchestrator",
    "model": null,
    "tool": null
  }
}
```

### 20.2 必填字段

MVP 阶段 Event Log 必须包含：

1. `event_id`；
2. `run_id`；
3. `task_id`；
4. `timestamp`；
5. `event_type`；
6. `node_id`；
7. `node_type`；
8. `input_refs`；
9. `output_refs`；
10. `status`；
11. `duration_ms`；
12. `error`；
13. `warnings`。

`metadata` 为可选字段。

### 20.3 event_type 枚举

MVP 支持以下事件类型：

```text
run_started
run_completed
run_failed
node_started
node_completed
node_failed
model_called
tool_called
evidence_created
analysis_domain_job_dispatched
analysis_card_created
validation_report_created
conflict_report_created
playbook_evaluation_report_created
guardrail_report_created
resolved_decision_bounds_created
decision_candidate_created
decision_trace_created
user_feedback_recorded
```

### 20.4 node_type 枚举

```text
workflow_node
analysis_domain
model
tool
agent
evaluator
guardrail
orchestrator
user_action
```

### 20.5 status 枚举

```text
success
failed
skipped
partial
blocked
warning
```

### 20.6 Decision Trace 对 Event Log 的依赖

Decision Trace 不需要展示完整 Event Log，但必须能从 Event Log 追溯以下问题：

1. 用户输入了什么任务；
2. 系统执行了哪些 Workflow 节点；
3. 生成了哪些 Evidence Packets；
4. 调度了哪些 Analysis Domain Jobs；
5. 生成了哪些 Analysis Cards；
6. 哪些 Validation / Conflict / Playbook / Guardrail 节点改变了建议边界；
7. Decision Candidate 是基于哪些上游对象生成的；
8. 是否发生错误、跳过、降级或人工复核标记。

### 20.7 MVP 必须记录的事件

MVP 标准单股票分析至少记录：

1. `run_started`；
2. `node_completed: parse_investment_task`；
3. `node_completed: load_investment_playbook`；
4. `node_completed: build_context_bundle`；
5. `evidence_created`；
6. `analysis_domain_job_dispatched`；
7. `analysis_card_created`；
8. `validation_report_created`；
9. `conflict_report_created`；
10. `playbook_evaluation_report_created`；
11. `guardrail_report_created`；
12. `resolved_decision_bounds_created`；
13. `decision_candidate_created`；
14. `decision_trace_created`；
15. `run_completed` 或 `run_failed`。

如果系统输出 `analysis_incomplete`，也必须记录对应原因事件。

---

## 21. 数据新鲜度与时效性策略

每个数据对象至少包含：

```json
{
  "as_of": "2026-06-14",
  "collected_at": "2026-06-14T10:30:00Z",
  "valid_until": "2026-06-14T16:00:00Z",
  "freshness_level": "intraday",
  "staleness_risk": "medium"
}
```

新鲜度分级：

```text
real_time
intraday
daily
quarterly
event_based
static
```

缓存策略：

1. real_time / intraday 默认重拉；
2. daily 当天可复用；
3. quarterly 在新财报前复用；
4. event_based 检查是否有新增事件；
5. static 长期复用。

---

## 22. 标准单股票 Workflow

Workflow 名称：

```text
single_stock_standard_analysis_workflow
```

步骤：

```text
START
  ↓
1. Parse Investment Task
  ↓
2. Load Investment Playbook
  ↓
3. Build Context Bundle
  ↓
4. Generate Evidence Packets
  ↓
5. Dispatch Analysis Domain Jobs
  ↓
6. Collect Analysis Cards
  ↓
7. Post-card Validation
  ↓
8. Detect Cross-domain Conflicts
  ↓
9. Pre-decision Validation
  ↓
10. Evaluate Playbook Conditions
  ↓
11. Run Guardrail Check
  ↓
12. Resolve Decision Bounds
  ↓
13. Generate Decision Candidate
  ↓
14. Build Decision Trace
  ↓
END
```

默认 Playbook：

```text
capital_cycle_fundamental_playbook
```

完整 Playbook 结构由 SPEC-006 定义。MVP 阶段可以使用内置静态版本。

---

## 23. 最小可用 Analysis Card 阈值

生成完整 Decision Candidate 至少满足：

1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals Card 必须可用；
3. 至少一个非 Fundamentals 的能力域提供有效支持或反方证据；
4. 不存在 Block 级 Validation Finding；
5. Playbook 关键 Hard Constraint 可以在 Playbook Evaluation 阶段被判断。

Pre-decision Validation 只检查前四项。第 5 项由 Playbook Evaluation 自行处理。

未达到阈值时，系统应输出：

```text
run_status = analysis_incomplete
```

或要求用户补充数据。

---

## 24. 系统状态与建议动作的语义分离

`analysis_incomplete` 和 `need_more_data` 不应混用。

### 24.1 系统状态

系统状态表示工作流是否完成。

```json
{
  "run_status": "analysis_incomplete"
}
```

可选值包括：

```text
pending
running
completed
completed_with_warnings
analysis_incomplete
failed
requires_user_input
requires_human_review
```

`analysis_incomplete` 表示系统无法生成完整 Decision Candidate。

### 24.2 建议动作

建议动作表示对用户的投资研究建议。

```json
{
  "suggested_action": "need_more_data"
}
```

`need_more_data` 只能作为用户可见建议动作，表示建议用户补充更多数据后再判断。

当系统未达到最小分析阈值时：

```json
{
  "run_status": "analysis_incomplete",
  "decision_candidate": null
}
```

系统可以生成一个非投资建议型说明，但不得将其包装成完整 Decision Candidate。

---

## 25. Playbook Lifecycle

每次 Decision Trace 必须记录：

1. playbook_id；
2. playbook_version；
3. playbook_snapshot_hash，若可用；
4. playbook_source。

MVP 阶段可以不实现完整 Playbook 历史版本仓库。

但如果 Playbook 是内置静态版本，则应至少记录：

```json
{
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_source": "built_in_static",
  "playbook_snapshot_hash": "sha256:..."
}
```

完整 Playbook 生命周期管理由 SPEC-006 定义。

---

## 26. Review & Governance

### 26.1 Evaluator

Evaluator 在 MVP 中只做检查、标注和阻断，不做自动重写。

输出进入 Validation Report。

### 26.2 Guardrail Checker

MVP 阶段强制实现前置 Guardrail。

后置 Guardrail 可以留作后续版本，用于检查最终用户可见表达是否越界，例如是否承诺收益、是否出现无依据强建议、是否隐藏反方证据、是否把模型预测表述为确定事实。

完整机制由 SPEC-009 定义。

### 26.3 Human-in-the-loop

以下场景应触发或建议人工复核：

1. High conflict；
2. Guardrail Block；
3. Validation Block；
4. Playbook Evaluation 返回 requires_human_review；
5. 关键数据缺失但用户仍要求结论；
6. 重大突发事件或数据冲突。

---

## 27. Observability 与 Decision Trace

底层维护统一 Event Log。

基于 Event Log 生成两个视图：

1. Observability View：面向开发者、运维和系统评估；
2. Decision Trace View：面向投资用户和投研复盘。

两者共享数据源，但展示目标、筛选规则和受众不同。

---

## 28. Macro / Meso MVP 实现层级

MVP 保留 Macro / Meso 一级能力域，但不做完整宏观研究系统。

MVP 范围：

1. Market Regime Context；
2. Industry / Capex Cycle Context；
3. Rate / Liquidity / Policy Context。

优先使用：

1. 外部数据源已有指标；
2. 人工维护或半结构化标签；
3. 简单规则模型；
4. 明确来源的政策或行业信息；
5. 少量 Agentic 解释。

不做自主宏观预测、复杂 regime 推断、完整行业供需模型、宏观资产配置模型或隐含宏观因子回归。

Macro / Meso Card 在 MVP 中常见状态为：

```json
{
  "domain_status": "partial",
  "data_quality": "medium"
}
```

这表示该能力域可用于背景解释、风险提示或辅助判断，但不应单独支撑强建议。

---

## 29. Sentiment MVP 降权策略

Sentiment 保留为一级能力域，但默认视为高噪声能力域。

如果数据质量 low：

1. 标记低数据质量；
2. 降低默认置信度；
3. 不作为强建议主要依据；
4. 不允许单独触发 buy / sell；
5. 主要用于风险提示、过热提示、叙事观察。

Sentiment Card 当 `data_quality = low` 时，默认应使用：

```json
{
  "domain_status": "partial",
  "data_quality": "low"
}
```

Sentiment 默认回答：

1. 是否过热；
2. 是否恐慌；
3. 是否叙事拥挤；
4. 是否与基本面或事件背离；
5. 是否需要谨慎追高或抄底。

---

## 30. MVP 架构边界

MVP 应实现：

1. 单股票标准 Workflow；
2. Investment Task 解析；
3. 默认 Playbook；
4. Context Bundle；
5. Evidence Packet；
6. 五个能力域 Analysis Card；
7. Validation Reports；
8. Conflict Reports；
9. Playbook Evaluation Report；
10. Guardrail Report；
11. Resolved Decision Bounds；
12. Decision Candidate；
13. Decision Trace Level 1 / Level 2；
14. 基础 Event Log；
15. 数据时效性标记；
16. 最小卡片阈值判断。

MVP 暂不实现：

1. 用户自由编辑复杂 Playbook；
2. 多股票批量扫描；
3. 组合优化；
4. 自动交易；
5. 实盘订单接入；
6. Bull / Bear 多 Agent 辩论；
7. Evaluator 自动重写；
8. 完整 Observability Dashboard；
9. 完整 Case Library；
10. Playbook Applicability Evaluator；
11. 复杂宏观预测；
12. 完整行业供需模型。

---

## 31. 错误与降级策略

### 31.1 数据缺失

若关键数据缺失，不应强行生成完整 Decision Candidate。

应输出：

```text
analysis_incomplete
```

或提示用户补充数据。

### 31.2 能力域失败

若单个非关键能力域失败，可继续执行，但必须：

1. 标记该能力域 `domain_status = failed`；
2. 进入 Decision Trace；
3. 降低最终置信度；
4. 不让该能力域参与 Conflict Detection。

若 Fundamentals Card 失败，则默认不生成完整 Decision Candidate。

### 31.3 Guardrail Block

若 Guardrail 触发 Block，系统必须阻止强建议，并可将输出降级为 `analysis_incomplete` 或 `requires_human_review`。

### 31.4 allowed_actions 为空

若 Resolved Decision Bounds 的 `allowed_actions` 为空，不生成完整 Decision Candidate。

---

## 32. Run State

```json
{
  "run_id": "run_001",
  "task": "InvestmentTask",
  "playbook": "PlaybookContext",
  "context_bundle": "ContextBundle",
  "evidence_packets": [],
  "analysis_domain_jobs": [],
  "analysis_cards": [],
  "validation_reports": [],
  "conflict_reports": [],
  "playbook_evaluation_report": null,
  "guardrail_report": null,
  "resolved_decision_bounds": null,
  "decision_candidate": null,
  "decision_trace": null,
  "event_log": [],
  "status": "running"
}
```

MVP 阶段 `playbook_evaluation_report` 保持单值。未来支持多 Playbook 对比时，应改为 `playbook_evaluation_reports: []`。

Run status 可选值：

```text
pending
running
completed
completed_with_warnings
analysis_incomplete
failed
requires_user_input
requires_human_review
```

---

## 33. 后续 SPEC 依赖

1. SPEC-004：五类分析能力域与 Analysis Card Schema；
2. SPEC-005：Capability Package 规范；
3. SPEC-006：Investment Playbook 规范；
4. SPEC-007：Orchestration 与执行路径；
5. SPEC-008：Decision Trace 与 Observability；
6. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
7. SPEC-011：Case Library 与历史案例记忆；
8. SPEC-012：数据治理与用户私有数据。

---

## 34. 开放问题

1. Playbook Applicability Evaluator 何时引入；
2. 置信度传播模型应由 SPEC-006 还是 SPEC-009 主导；
3. Metric Registry 完整 schema 应归入 SPEC-005 还是 SPEC-006；
4. 多股票批量扫描如何复用当前单股票 Workflow；
5. 用户私有数据进入 Case Library 的权限边界。

---

## 35. v0.3.3 总结

SPEC-003 v0.3.3 是当前完整架构基准版。

本版本完成以下关键闭环：

1. 七层职责分层；
2. 核心对象链；
3. Evidence Packet 生成机制分类；
4. 能力域独立性约束；
5. Analysis Card 与 domain_status；
6. Playbook Constraint 与 input_refs；
7. Hard Constraint 确定性污染边界；
8. 两阶段 Validation；
9. Conflict escalation rules；
10. Playbook Evaluation Report；
11. Guardrail Report；
12. Resolved Decision Bounds 正式 schema；
13. Decision Candidate 集合隶属约束；
14. Event Log MVP schema；
15. Decision Trace 可审计链路。

本版本继续坚持 crosslens 的架构宪法：

```text
Deterministic first, Agentic when necessary, Traceable always.
```
