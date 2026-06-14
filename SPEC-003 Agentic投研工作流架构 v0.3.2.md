# SPEC-003：Agentic 投研工作流架构

**版本：** v0.3.2  
**状态：** Draft  
**项目名称：** crosslens  
**依赖文档：** SPEC-001 v0.4  
**文档类型：** 架构规格  
**目标阶段：** 产品机制设计 / MVP 架构定义  

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

这些冲突应进入 Conflict Report，并影响 Decision Candidate 的建议边界。

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

示例：

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

可选值：

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

示例：

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

Structured Evidence 由专门模型、分类器、规则模型或半结构化抽取器生成。它有明确输入输出和置信度，但可能有误差，需要记录模型版本。

示例包括公司事件分类、情绪标签、新闻主题分类、宏观 regime 标签、行业周期阶段、风险事件识别、财报语气变化和管理层指引变化。

### 7.3 Interpreted Evidence

Interpreted Evidence 由 Agentic Reasoning 或 LLM 解释生成。它不完全可复现，依赖上下文和模型，不应作为硬性规则的唯一依据。

Interpreted Evidence 必须标记：

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

示例：

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

`constraint://...` URI 格式为示意。实际 Playbook Constraint URI 和版本解析规则由 SPEC-006 定义。

---

## 9. 能力域独立性约束

MVP 阶段五个能力域可以串行执行，也可以并行执行。但无论物理执行顺序如何，能力域之间必须逻辑独立。

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

能力域运行时不得访问其他能力域运行状态。该约束应由编排框架、运行时上下文隔离或任务输入白名单保证。

---

## 10. Analysis Card

Analysis Card 是每个能力域向编排器返回的标准化分析结果。

### 10.1 domain_status

Analysis Card 必须包含 `domain_status` 字段。

可选值：

```text
completed
partial
insufficient_data
failed
skipped
```

语义：

| domain_status | 含义 | 下游处理 |
|---|---|---|
| completed | 能力域正常完成分析 | 可进入 Conflict Detection、Playbook Evaluation |
| partial | 能力域部分完成，但存在数据缺口或低置信度 | 可进入下游，但必须标记警告 |
| insufficient_data | 数据不足，无法形成有效分析 | 不计入最小可用卡片阈值 |
| failed | 能力域执行失败 | 不进入 Conflict Detection，进入 Decision Trace 错误说明 |
| skipped | 编排器主动跳过该能力域 | 不计入最小可用卡片阈值 |

`skipped` 表示系统主动选择不运行该能力域，例如：

1. 用户选择的 Playbook 不需要该域；
2. 编排器根据任务类型路由跳过该域；
3. 用户手动关闭该域；
4. 专项分析工作流不需要该域。

`skipped` 与 `insufficient_data` 的区别是：前者是主动跳过，后者是被动数据不足。Decision Trace 必须区分展示二者。

### 10.2 confidence

Analysis Card 应包含 `confidence` 字段，但其格式、计算来源和聚合规则由 SPEC-004 定义。

本 SPEC 不预决 Analysis Card confidence 的计算方式。

---

## 11. Playbook Constraint input_refs 引用规范

`input_refs` 是 Playbook Hard Constraint 能否机器执行的关键。

`input_refs` 不应是任意字符串，而应引用可解析的 Evidence Value 或 Metric Registry 条目。

### 11.1 MVP 引用模型

MVP 阶段支持两种引用方式。

#### A. Evidence Value Reference

直接引用 Evidence Packet 中的某个结构化值。

格式：

```text
evidence://{evidence_id}/{value_path}
```

示例：

```text
evidence://ev_financial_001/metrics.revenue_growth
evidence://ev_valuation_001/metrics.pe_percentile_5y
evidence://ev_technical_001/metrics.rsi_14d
```

#### B. Metric Reference

引用系统统一 Metric Registry 中的指标名。

格式：

```text
metric://{metric_id}
```

示例：

```text
metric://revenue_growth_ttm
metric://industry_median_revenue_growth_ttm
metric://gross_margin_qoq_change
metric://pe_percentile_5y
```

Metric Registry 负责解析该指标来自哪个 Evidence Packet、哪个数据源、哪个时间戳。

### 11.2 Metric Registry MVP 最小形态

MVP 阶段必须提供 Metric Registry 的最小实现，用于支持 Playbook Constraint 的 `metric://` 引用。

MVP Metric Registry 可以是一个静态 JSON 映射表。

示例：

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

最小字段：

1. metric_id；
2. display_name；
3. value_type；
4. unit；
5. source_domain；
6. preferred_evidence_type；
7. evidence_value_path；
8. freshness_requirement；
9. required_for_hard_constraint。

完整 Metric Registry 设计由 SPEC-005 或 SPEC-006 定义。

### 11.3 引用解析要求

规则引擎执行 Hard Constraint 前，必须解析每个 `input_ref`，并获得：

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

---

## 12. Hard Constraint 与证据确定性

Hard Constraint 的执行逻辑可以是确定性的，但它所引用的输入不一定完全确定。

### 12.1 默认规则

Hard Constraint 默认只能引用 `determinism_level = computed` 的 metrics。

如果 Hard Constraint 引用了 Structured Evidence 的 metrics，系统必须：

1. 将该 Constraint 标记为 `conditional_hard_constraint`；
2. 继承上游 evidence 的 confidence 和 data_quality；
3. 不允许该结果单独支撑 strong buy / strong sell；
4. 在 Decision Trace 中明确说明该 Hard Constraint 的输入来自 Structured Evidence。

如果 Hard Constraint 引用了 Interpreted Evidence：

1. 默认不得作为唯一输入；
2. 除非用户或系统显式允许；
3. 必须触发 Flag；
4. 不得支持强建议。

中文表达：

> 基于不确定证据执行的确定性规则，不能被视为完全确定的判断。

完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

---

## 13. Validation Report 两阶段接入机制

v0.3.2 将 Validation 明确为两阶段。

### 13.1 Post-card Validation

Post-card Validation 在 Analysis Cards 收集后立即执行。

输入：

1. Analysis Card List；
2. Evidence Packet List。

主要检查：

1. Analysis Card 是否缺少必要字段；
2. 是否缺少 supporting_evidence；
3. 是否缺少 opposing_evidence；
4. evidence_refs 是否有效；
5. data_quality 是否缺失；
6. domain_status 是否有效；
7. 是否存在无证据判断；
8. 是否存在过度自信表述。

### 13.2 Post-card Validation Block 后的 Card 处理

Post-card Validation 不直接修改 Analysis Card。

如果某张 Analysis Card 被 Validation Report 标记为 Block，Conflict Detection 必须通过 Validation Report 过滤该 Card。

推荐 finding：

```json
{
  "finding_id": "finding_001",
  "severity": "block",
  "target_ref": "card_sentiment_001",
  "finding_type": "unsupported_claim",
  "recommended_handling": "exclude_from_conflict_detection"
}
```

Conflict Detection 在运行前必须读取 Post-card Validation Report，并执行：

1. Block 级 Card 不参与 Conflict Detection；
2. Flag 级 Card 可以参与，但降低可信度；
3. Note 级 Card 正常参与；
4. 被排除的 Card 必须进入 Decision Trace。

Analysis Card 的 `domain_status` 表示能力域自我报告状态；Validation Report 表示外部质量检查结果。两者不得混用。

### 13.3 Pre-decision Validation

Pre-decision Validation 在 Conflict Detection 之后、Playbook Evaluation 之前执行。

输入：

1. Analysis Cards；
2. Conflict Reports；
3. Post-card Validation Report。

主要检查：

1. 是否存在未解释的高严重度冲突；
2. 模块冲突是否被充分暴露；
3. 是否达到最小 Analysis Card 阈值；
4. Fundamentals Card 是否可用；
5. 是否存在必须阻止 Decision Candidate 的 Block；
6. 是否需要人工复核；
7. 是否应将最终输出降级为 analysis_incomplete。

### 13.4 Pre-decision Validation 与 Playbook Evaluation 职责边界

Pre-decision Validation 不应判断 Playbook Hard Constraint 是否可执行。

原因是：Playbook Evaluation Report 在 Pre-decision Validation 之后才生成。

Pre-decision Validation 只负责检查：

1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals Card 必须可用；
3. 至少一个非 Fundamentals 的能力域提供有效支持或反方证据；
4. 不存在 Block 级 Post-card Validation Finding；
5. 不存在未处理的 High Conflict。

Playbook Hard Constraint 是否可以被判断，由 Playbook Evaluation 阶段负责。

如果关键 Hard Constraint 无法解析或无法判断，Playbook Evaluation Report 应返回：

```text
overall_result = need_more_data
```

或：

```text
overall_result = requires_human_review
```

---

## 14. Conflict Report

Conflict Report 用于记录不同 Analysis Card 之间的冲突。

Conflict Report 不只是展示对象，也必须影响 Decision Candidate 的建议边界。

### 14.1 severity 初始赋值规则

Conflict severity 不应完全由 LLM 判断。

MVP 阶段应优先使用预定义规则表进行初始赋值。

影响 severity 的因素：

1. 涉及的能力域；
2. 是否涉及 Fundamentals；
3. 是否涉及 Playbook Hard Constraint；
4. 是否涉及 Guardrail；
5. 冲突双方的 confidence；
6. 证据类型是否为 Computed / Structured / Interpreted；
7. 数据质量；
8. 时间周期是否一致。

LLM 可以辅助解释冲突，但不应作为 severity 初始赋值的唯一来源。

---

## 15. Playbook Evaluation Report

Playbook Evaluation Report 是系统根据 Investment Playbook 对 Analysis Cards、Conflict Reports 和 Evidence Packets 进行条件检查后的结果。

它是 Decision Candidate 的直接输入之一。

### 15.1 impact_on_decision 枚举

每个 Playbook Condition 必须包含 `impact_on_decision` 字段。

可选值：

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

Playbook Evaluation Report 必须包含 `overall_result` 字段。

可选值：

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

Playbook Evaluation Report 必须说明 `recommended_decision_bounds` 如何从各个 Constraint 的 `impact_on_decision` 聚合而来。

MVP 阶段采用最严格约束交集规则。

#### 初始动作集合

默认候选动作集合：

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

MVP 阶段不建议使用：

```text
strong_buy
strong_sell
```

除非后续 SPEC 明确支持。

#### impact_on_decision 到动作约束的映射

| impact_on_decision | 动作约束 |
|---|---|
| support | 不移除动作，仅作为正向理由 |
| neutral | 不影响动作集合 |
| caution | 移除 buy，保留 wait / add_to_watchlist |
| lower_confidence | 不移除动作，但降低 confidence_cap |
| block_strong_buy | 移除 strong_buy，MVP 中等价于禁止高置信度买入表达 |
| block_strong_sell | 移除 strong_sell |
| block_new_position | 移除 buy |
| block_add_position | 移除 add_position，MVP 中可映射为禁止加仓表达 |
| require_human_review | 标记 requires_human_review = true |
| need_more_data | 若涉及关键 Hard Constraint，则 overall_result = need_more_data |

#### 聚合步骤

1. 从默认动作集合开始；
2. 按每个 Constraint 的 `impact_on_decision` 移除不允许动作；
3. 如果任一关键 Hard Constraint 返回 `need_more_data`，则整体 `overall_result = need_more_data`；
4. 如果多数关键 Hard Constraint fail，则整体 `overall_result = not_suitable_for_playbook`；
5. 如果存在 `require_human_review`，则整体标记 `requires_human_review = true`；
6. 最终剩余动作集合写入 `recommended_decision_bounds`。

---

## 16. Guardrail Report

Guardrail Report 是系统边界检查结果，用于确保系统不输出越界、不可靠或过度自信的投资建议。

MVP 阶段只强制实现前置 Guardrail。后置 Guardrail 可留作后续版本，用于检查最终用户可见表达是否越界。

---

## 17. Resolved Decision Bounds

Decision Candidate 生成前，系统必须合并多个约束来源。

约束优先级如下：

```text
Guardrail Block
  >
Validation Block
  >
Playbook Evaluation recommended_decision_bounds
  >
Conflict severity restriction
  >
Soft preference / style guidance
```

### 17.1 非 Block Guardrail 的降级语义

如果 Guardrail 不是 Block，但包含 `downgrade_decision_bounds`，则应影响 Resolved Decision Bounds。

处理规则：

1. 从 `allowed_actions` 中移除强建议动作，例如 `buy`、`strong_buy`、`add_position`；
2. 保留谨慎动作，例如 `wait`、`add_to_watchlist`、`hold_if_already_owned`；
3. 降低 `confidence_cap`；
4. 在 Decision Trace 中展示 Guardrail 降级原因。

完整 Guardrail action 语义由 SPEC-009 定义。

### 17.2 confidence_cap 来源记录

Resolved Decision Bounds 中的 `confidence_cap` 必须记录来源。

示例：

```json
{
  "confidence_cap": 0.62,
  "confidence_cap_reason": [
    {
      "source_type": "validation_report",
      "source_ref": "val_pre_decision_001",
      "reason": "存在 Flag 级数据质量问题",
      "effect": "cap_confidence_at_0.75"
    },
    {
      "source_type": "conflict_report",
      "source_ref": "conflict_001",
      "reason": "存在 medium severity 跨域冲突",
      "effect": "cap_confidence_at_0.68"
    },
    {
      "source_type": "guardrail_report",
      "source_ref": "gr_001",
      "reason": "Sentiment 数据质量低，禁止高置信度表达",
      "effect": "cap_confidence_at_0.62"
    }
  ]
}
```

MVP 阶段不要求复杂置信度传播模型，但必须满足：

1. `confidence_cap` 不得由 LLM 随机生成；
2. 每一次 confidence 降级必须有来源；
3. 最终 Decision Candidate 的 `confidence` 不得高于 `confidence_cap`；
4. 完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

---

## 18. Decision Candidate

Decision Candidate 是系统生成的投资判断候选。

它不是最终用户决策，而是系统在某个 Playbook 下给出的建议。

Decision Candidate 必须显式引用上游约束对象。

示例：

```json
{
  "candidate_id": "decision_001",
  "task_id": "task_001",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_evaluation_report_id": "pbe_001",
  "guardrail_report_id": "gr_001",
  "validation_report_refs": [
    "val_post_card_001",
    "val_pre_decision_001"
  ],
  "conflict_report_refs": [
    "conflict_001"
  ],
  "resolved_decision_bounds_id": "rdb_001",
  "suggested_action": "wait",
  "action_selection_reason": "Playbook Evaluation 禁止新开仓，Guardrail 禁止强买入，因此从 allowed_actions 中选择 wait。",
  "confidence": 0.62,
  "requires_human_review": false
}
```

---

## 19. 系统状态与建议动作的语义分离

`analysis_incomplete` 和 `need_more_data` 不应混用。

`analysis_incomplete` 是系统状态，表示系统无法生成完整 Decision Candidate。

`need_more_data` 是用户可见建议动作，表示建议用户补充更多数据后再判断。

当系统未达到最小分析阈值时：

```json
{
  "run_status": "analysis_incomplete",
  "decision_candidate": null
}
```

系统可以生成一个非投资建议型说明：

```json
{
  "message_type": "analysis_incomplete_notice",
  "suggested_next_step": "need_more_data"
}
```

但不得将其包装成完整 Decision Candidate。

---

## 20. 标准单股票 Workflow

MVP 推荐优先实现标准单股票分析 Workflow。

Workflow 名称：

```text
single_stock_standard_analysis_workflow
```

v0.3.2 推荐 Workflow 顺序如下：

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

---

## 21. 最小可用 Analysis Card 阈值

MVP 阶段不应在信息不足时强行生成 Decision Candidate。

生成 Decision Candidate 至少需要满足：

1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals Card 必须可用；
3. 至少一个非 Fundamentals 的能力域提供有效支持或反方证据；
4. 不存在 Block 级 Post-card Validation Finding；
5. 不存在未处理的 High Conflict。

Playbook Hard Constraint 是否可以被判断，不属于 Pre-decision Validation 阈值，而由 Playbook Evaluation 阶段处理。

---

## 22. Macro / Meso 与 Sentiment MVP 降权策略

Macro / Meso 和 Sentiment 在 MVP 中可能由于数据噪声、覆盖不足或能力降级，默认返回：

```text
domain_status = partial
```

这不表示能力域失败，而表示：

1. 该能力域输出可用于背景解释、风险提示或辅助判断；
2. 不应作为强建议的主要依据；
3. 不应单独触发 buy / sell；
4. 必须在 Decision Trace 中标记降权原因。

尤其是 Sentiment Card，当 `data_quality = low` 时，默认应使用：

```json
{
  "domain_status": "partial",
  "data_quality": "low"
}
```

---

## 23. Run State

每次工作流运行应维护 Run State。

示例：

```json
{
  "run_id": "run_001",
  "run_status": "running",
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
  "event_log": []
}
```

MVP 阶段 `playbook_evaluation_report` 保持单值，因为 MVP 只支持单一 Playbook 执行路径。

未来如果支持多 Playbook 对比，应改为：

```json
{
  "playbook_evaluation_reports": []
}
```

---

## 24. MVP 架构边界

### 24.1 MVP 应实现

1. 单股票标准分析 Workflow；
2. Investment Task 解析；
3. 默认 Investment Playbook；
4. Context Bundle 构建；
5. Evidence Packet 生成；
6. 五个分析能力域返回 Analysis Card；
7. Post-card Validation；
8. Conflict Detection；
9. Pre-decision Validation；
10. Playbook Evaluation；
11. Guardrail Check；
12. Resolved Decision Bounds；
13. Decision Candidate；
14. Decision Trace Level 1 和 Level 2；
15. 基础 Event Log；
16. Metric Registry 最小静态映射；
17. recommended_decision_bounds 聚合规则。

### 24.2 MVP 暂不实现

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
11. 复杂宏观预测系统；
12. 完整行业供需模型；
13. 完整置信度传播模型。

---

## 25. 后续 SPEC 依赖

1. SPEC-004：五类分析能力域与 Analysis Card Schema；
2. SPEC-005：Capability Package 与 Metric Registry 规范；
3. SPEC-006：Investment Playbook 规范；
4. SPEC-007：Orchestration 与执行路径；
5. SPEC-008：Decision Trace 与 Observability；
6. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
7. SPEC-011：Case Library 与历史案例记忆；
8. SPEC-012：数据治理与用户私有数据。

---

## 26. SPEC-003 v0.3.2 总结

SPEC-003 v0.3.2 的核心目标是让 crosslens 的工作流架构更接近 MVP 可实现状态。

本版本补齐：

1. SPEC-001 v0.4 的七层架构对齐；
2. Hard Constraint 默认只能引用 Computed Evidence metrics；
3. Structured Evidence metrics 用于约束时必须标记为 conditional_hard_constraint；
4. Analysis Card confidence 的具体定义交由 SPEC-004；
5. `domain_status = skipped` 的语义；
6. `user_private_data_types`；
7. `constraint://...` URI 的示意性质；
8. 能力域执行隔离；
9. Metric Registry 的 MVP 最小形态；
10. `recommended_decision_bounds` 的 MVP 聚合规则；
11. `facts` 与 `metrics` 的字段区分；
12. 后置 Guardrail 的 MVP 边界；
13. Macro / Meso 与 Sentiment 的 partial 状态语义。

v0.3.2 继续坚持 crosslens 的架构宪法：

> **Deterministic first, Agentic when necessary, Traceable always.**
