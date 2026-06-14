# SPEC-003：Agentic 投研工作流架构

**版本：** v0.3.1  
**状态：** Draft  
**项目名称：** crosslens  
**依赖文档：** SPEC-001 v0.3  
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

系统不应让一个超级 Agent 自由决定全部流程，也不应把所有步骤都写死为不可变流水线。

crosslens SPEC-003 的架构宪法是：

> **Deterministic first, Agentic when necessary, Traceable always.**

中文表达：

> **确定性优先；必要时才使用 Agentic 推理；全过程必须可追踪。**

该原则是 crosslens 工作流架构的核心约束。

---

## 3. 设计原则

### 3.1 Workflow first, Agent when needed

能用确定性流程、规则、指标、模型或工具解决的问题，不强行使用 Agent。

Agent 主要用于：

1. 开放式解释；
2. 事件影响路径分析；
3. 冲突归因；
4. 反方观点生成；
5. 不确定性表达；
6. 用户问题追问；
7. 投资语境化解释。

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

其中，Playbook Hard Constraint 的规则执行本身应是确定性的，但结果确定性取决于输入证据类型。若 Hard Constraint 引用 Structured Evidence 或 Interpreted Evidence，必须继承上游证据的不确定性，详见第 12 节。

### 3.4 编排器不侵入能力域内部实现

编排器调度全局 Workflow 节点和能力域级 Analysis Domain Job。

编排器不直接调度能力域内部的模型、工具、Agent 或子 Workflow。

能力域内部如何组合模型、工具、Workflow、Agent、Evaluator，由该能力域自行定义。

编排器只依赖能力域暴露的标准接口：

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

例如：

1. 基本面正面，但估值过高；
2. 技术面趋势良好，但情绪过热；
3. 宏观环境压制估值，但公司事件催化强。

这些冲突应进入 Conflict Report，并影响 Decision Candidate 的建议边界。

### 3.6 Playbook 约束判断，不替代证据

Investment Playbook 表达用户或系统的投资风格和决策偏好。

Playbook 不应替代事实和证据生成，而应在三个阶段发挥作用：

1. 前置：影响分析重点；
2. 中置：约束 Analysis Card 的检查项；
3. 后置：参与 Decision Candidate 生成。

### 3.7 用户保留最终控制权

系统可以生成投资判断建议，但不替代用户做最终投资决策。

MVP 阶段不做自动下单，不做收益承诺，不做黑箱荐股。

---

## 4. 七层架构

crosslens 的 Agentic 投研工作流采用七层架构：

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

编排器从任务启动开始就负责驱动整个 Workflow，包括：

1. 任务解析；
2. Playbook 加载；
3. Context Bundle 构建；
4. Evidence Packet 生成；
5. Analysis Domain Job 调度；
6. Validation；
7. Conflict Detection；
8. Playbook Evaluation；
9. Guardrail Check；
10. Decision Candidate 生成；
11. Decision Trace 构建。

因此，Workflow 中出现 Build Context Bundle 和 Generate Evidence Packets，并不表示这些步骤绕过了 Orchestrator。

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
  "uses_user_private_data": false,
  "created_at": "2026-06-14T00:00:00Z"
}
```

### 6.2 Context Bundle

Context Bundle 是执行任务所需的上下文集合。

它可以包含：

1. 市场行情；
2. 财务数据；
3. 公司公告；
4. 公司新闻；
5. 宏观/中观背景；
6. 社媒和情绪数据；
7. 技术指标原始数据；
8. 用户持仓；
9. 用户历史分析记录；
10. Playbook 配置；
11. 相关历史案例。

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

| data_quality | 含义 |
|---|---|
| high | 数据源可靠、字段完整、时效性满足任务要求 |
| medium | 数据可用，但存在轻微缺失、延迟或覆盖不足 |
| low | 数据噪声高、覆盖不足、来源不稳定或置信度低 |
| unavailable | 数据不可用 |
| unknown | 系统无法判断数据质量 |

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

示例：

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

示例：

```json
{
  "facts": [
    "company_announced_capacity_expansion",
    "management_guidance_lowered",
    "sentiment_state_overheated"
  ]
}
```

Hard Constraint 优先引用 `metrics`。

Soft Constraint 可以引用 `facts`，但必须保留 evidence_refs。

---

## 7. Evidence Packet 生成机制分类

Evidence Packet 不应默认由 LLM 生成。

每个 Evidence Packet 必须标记其生成机制。

### 7.1 Computed Evidence

Computed Evidence 由确定性计算、规则或数据接口生成。

特点：

1. 可复现；
2. 可测试；
3. 可审计；
4. 不依赖 LLM 推理；
5. 优先级最高。

示例：

1. 财务比率；
2. 收入增速；
3. 毛利率变化；
4. 自由现金流率；
5. PE / PB / EV/EBITDA 分位；
6. RSI / MACD / ATR；
7. 成交量放大倍数；
8. 价格相对均线位置；
9. 是否跌破关键均线；
10. 数据是否缺失。

### 7.2 Structured Evidence

Structured Evidence 由专门模型、分类器、规则模型或半结构化抽取器生成。

特点：

1. 有明确输入输出；
2. 有置信度；
3. 可评估；
4. 可能有误差；
5. 需要记录模型版本。

示例：

1. 公司事件分类；
2. 情绪标签；
3. 新闻主题分类；
4. 宏观 regime 标签；
5. 行业周期阶段；
6. 风险事件识别；
7. 财报语气变化；
8. 管理层指引变化。

### 7.3 Interpreted Evidence

Interpreted Evidence 由 Agentic Reasoning 或 LLM 解释生成。

特点：

1. 不完全可复现；
2. 依赖上下文和模型；
3. 需要明确标记；
4. 不应作为硬性规则的唯一依据；
5. 必须进入 Decision Trace 的不确定性说明。

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

一个重大政策事件的 Interpreted Evidence 可能投资重要性很高，但仍需标记为解释性判断。

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

跨域信息融合只能发生在编排器控制的后处理节点中：

1. Conflict Detection；
2. Validation；
3. Playbook Evaluation；
4. Decision Bounds Resolution；
5. Decision Candidate Generation。

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

| domain_status | 含义 | 下游处理 |
|---|---|---|
| completed | 能力域正常完成分析 | 可进入 Conflict Detection、Playbook Evaluation |
| partial | 能力域部分完成，但存在数据缺口或低置信度 | 可进入下游，但必须降低权重或标记警告 |
| insufficient_data | 数据不足，无法形成有效分析 | 不计入最小可用卡片阈值 |
| failed | 能力域执行失败 | 不进入 Conflict Detection，进入 Decision Trace 错误说明 |
| skipped | 编排器根据任务或 Playbook 主动跳过 | 不计入最小可用卡片阈值 |

### 10.2 Analysis Card 示例

```json
{
  "card_id": "card_fundamentals_001",
  "task_id": "task_001",
  "domain": "fundamentals",
  "domain_status": "completed",
  "summary": "基本面偏正面，但估值压力较高",
  "stance": "moderately_positive",
  "confidence": 0.66,
  "time_horizon": "6-12 months",
  "supporting_evidence": [
    {
      "evidence_id": "ev_financial_001",
      "description": "收入增速高于行业中位数"
    }
  ],
  "opposing_evidence": [
    {
      "evidence_id": "ev_valuation_001",
      "description": "估值位于过去五年较高分位"
    }
  ],
  "key_risks": [
    "估值压缩风险",
    "增长放缓风险"
  ],
  "invalidating_conditions": [
    "下季度收入增速低于行业中位数"
  ],
  "data_quality": "medium",
  "warnings": []
}
```

Analysis Card 的完整 schema 由 SPEC-004 定义。

---

## 11. Playbook Constraint 与 input_refs 引用规范

Playbook Constraint 是 Investment Playbook 中可被系统执行或解释的条件。

### 11.1 Constraint 最小结构

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

### 11.2 Hard Constraint

Hard Constraint 必须由规则引擎或确定性逻辑执行。

适用对象：

1. 数值阈值；
2. 趋势方向；
3. 存在性检查；
4. 数据缺失检查；
5. 仓位或风险硬限制；
6. 明确禁止条件。

Hard Constraint 不应由 LLM 直接判断。

### 11.3 Soft Constraint

Soft Constraint 可以由 LLM 辅助解释，但必须保留证据引用。

适用对象：

1. 事件影响路径；
2. 宏观环境适配；
3. 叙事是否过热；
4. 管理层表述变化；
5. 行业周期阶段判断。

Soft Constraint 的结果必须标记不确定性。

### 11.4 input_refs 引用模型

`input_refs` 不应是任意字符串，而应引用可解析的 Evidence Value 或 Metric Registry 条目。

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

### 11.5 引用解析要求

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

如果任一必要引用无法解析，该 Constraint 状态应为：

```text
insufficient_data
```

并触发 `on_insufficient_data` 处理路径。

---

## 12. Hard Constraint 的确定性污染风险

Hard Constraint 的执行逻辑可以是确定性的，但它所引用的输入不一定完全确定。

例如：

```text
Market Regime = tightening
Industry Cycle = early_recovery
Sentiment State = overheated
```

这些可能来自 Structured Evidence，而不是 Computed Evidence。

因此，系统必须区分：

```text
规则执行的确定性
输入证据的确定性
```

即：

```text
A deterministic rule over uncertain evidence is not fully deterministic.
```

中文表达：

```text
基于不确定证据执行的确定性规则，不能被视为完全确定的判断。
```

### 12.1 MVP 处理原则

如果 Hard Constraint 引用了 Structured Evidence：

1. Constraint 可以由规则引擎执行；
2. 但结果必须继承上游证据的不确定性；
3. `confidence` 不得默认为 1.0；
4. Decision Trace 必须标记该 Hard Constraint 的输入并非 Computed Evidence；
5. 不允许将该结果表述为绝对事实。

如果 Hard Constraint 引用了 Interpreted Evidence：

1. 默认不得作为 Hard Constraint 的唯一输入；
2. 除非用户或系统显式允许；
3. 必须触发 Flag；
4. 不得支持 strong buy / strong sell。

完整的置信度传播模型由 SPEC-006 或后续治理 SPEC 定义。

---

## 13. Metric Registry 的 MVP 最小形态

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

Metric Registry 最小字段：

1. `metric_id`；
2. `display_name`；
3. `value_type`；
4. `unit`；
5. `source_domain`；
6. `preferred_evidence_type`；
7. `evidence_value_path`；
8. `freshness_requirement`；
9. `required_for_hard_constraint`。

完整 Metric Registry 设计由 SPEC-005 或 SPEC-006 定义。

---

## 14. Validation Report

Validation Report 是 Evaluator 对 Analysis Cards 或 Decision Candidate 相关上下文的质量检查结果。

Validation 不直接修改 Analysis Card，而是输出质量发现，并由 Orchestrator 消费。

### 14.1 两阶段 Validation

v0.3.1 明确采用两阶段 Validation：

1. Post-card Validation；
2. Pre-decision Validation。

### 14.2 Post-card Validation

Post-card Validation 在 Analysis Cards 收集后立即执行。

输入：

```text
Analysis Card List
Evidence Packet List
```

输出：

```text
Validation Report: post_card_validation
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

### 14.3 Post-card Validation Block 后的 Card 处理方式

Post-card Validation 不直接修改 Analysis Card。

如果某张 Analysis Card 被 Validation Report 标记为 Block，Conflict Detection 必须通过 Validation Report 过滤该 Card。

推荐结构：

```json
{
  "validation_report_id": "val_post_card_001",
  "validation_stage": "post_card_validation",
  "findings": [
    {
      "finding_id": "finding_001",
      "severity": "block",
      "target_ref": "card_sentiment_001",
      "finding_type": "unsupported_claim",
      "recommended_handling": "exclude_from_conflict_detection"
    }
  ]
}
```

Conflict Detection 在运行前必须读取 Post-card Validation Report，并执行：

1. Block 级 Card 不参与 Conflict Detection；
2. Flag 级 Card 可以参与，但降低可信度；
3. Note 级 Card 正常参与；
4. 被排除的 Card 必须进入 Decision Trace。

Analysis Card 的 `domain_status` 表示能力域自我报告状态；Validation Report 表示外部质量检查结果。两者不得混用。

### 14.4 Pre-decision Validation

Pre-decision Validation 在 Conflict Detection 之后、Playbook Evaluation 之前执行。

输入：

```text
Analysis Cards
Conflict Reports
Post-card Validation Report
```

输出：

```text
Validation Report: pre_decision_validation
```

主要检查：

1. 是否存在未解释的高严重度冲突；
2. 模块冲突是否被充分暴露；
3. 是否达到最小 Analysis Card 阈值；
4. Fundamentals Card 是否可用；
5. 是否存在必须阻止 Decision Candidate 的 Block；
6. 是否需要人工复核；
7. 是否应将最终输出降级为 analysis_incomplete。

### 14.5 Pre-decision Validation 与 Playbook Evaluation 的职责边界

Pre-decision Validation 不应判断 Playbook Hard Constraint 是否可执行。

原因是：Playbook Evaluation Report 在 Pre-decision Validation 之后才生成。

因此，Pre-decision Validation 只负责检查以下条件：

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

### 14.6 Finding severity

Validation Finding 必须分为三类：

1. Block：阻止继续生成强建议，或要求 Decision Candidate 降级；
2. Flag：不阻止工作流继续，但必须降低置信度，并进入 Decision Trace；
3. Note：仅记录，不影响 Decision Candidate。

### 14.7 overall_status 枚举

Validation Report 必须包含 `overall_status` 字段。

可选值：

```text
passed
passed_with_notes
passed_with_flags
blocked
failed
```

| overall_status | 含义 | 后续处理 |
|---|---|---|
| passed | 未发现问题 | 正常进入下一步 |
| passed_with_notes | 仅存在 Note 级问题 | 正常进入下一步，记录日志 |
| passed_with_flags | 存在 Flag 级问题，但无 Block | 继续执行，但降低置信度，并进入 Decision Trace |
| blocked | 存在 Block 级问题 | 不生成强 Decision Candidate，输出 analysis_incomplete |
| failed | Evaluator 自身执行失败 | 记录系统错误，允许工作流降级，但必须在 Decision Trace 中标记 |

---

## 15. Conflict Report

Conflict Report 用于记录不同 Analysis Card 之间的冲突。

示例：

```json
{
  "conflict_id": "conflict_001",
  "task_id": "task_001",
  "conflict_type": "fundamentals_vs_sentiment",
  "description": "基本面偏正面，但情绪信号显示短期过热",
  "involved_cards": [
    "card_fundamentals_001",
    "card_sentiment_001"
  ],
  "severity": "medium",
  "decision_implication": "不适合追高，适合等待回调或观察财报确认"
}
```

Conflict Report 不用于消除冲突，而用于展示冲突，并约束 Decision Candidate 的建议边界。

### 15.1 Conflict severity 初始赋值规则

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

#### Low

满足以下情况之一：

1. 冲突不涉及 Fundamentals；
2. 冲突不涉及 Hard Constraint；
3. 双方 confidence 均低；
4. 主要基于 low quality sentiment evidence。

#### Medium

满足以下情况之一：

1. Fundamentals 与 Technical / Sentiment 出现中等方向冲突；
2. Event 与 Sentiment 出现中等方向冲突；
3. Playbook Soft Constraint 与某个能力域结论冲突；
4. 冲突可能影响 suggested_action，但不阻止完整分析。

#### High

满足以下情况之一：

1. Fundamentals 与重大 Company Event 严重冲突；
2. Playbook Hard Constraint 与 Analysis Card 结论冲突；
3. Guardrail 相关风险与 Decision Candidate 倾向冲突；
4. 高置信度 Computed Evidence 与高置信度能力域结论冲突；
5. 冲突足以阻止强建议或要求人工复核。

LLM 可以辅助解释冲突，但不应作为 severity 初始赋值的唯一来源。

### 15.2 Conflict 对 Decision Candidate 的影响

#### Low Conflict

处理：

1. 正常生成 Decision Candidate；
2. 冲突进入 Decision Trace；
3. 置信度轻微下调。

#### Medium Conflict

处理：

1. 生成谨慎型 Decision Candidate；
2. 禁止 strong buy / strong sell 表达；
3. 建议动作优先使用 wait、add_to_watchlist、hold_if_already_owned；
4. 置信度中度下调。

#### High Conflict

处理：

1. 标记 requires_human_review；
2. 不生成强建议；
3. 输出 analysis_incomplete、wait 或 requires_human_review；
4. 在 Decision Trace 中突出显示冲突。

---

## 16. Playbook Evaluation Report

Playbook Evaluation Report 是系统根据 Investment Playbook 对 Analysis Cards、Conflict Reports 和 Evidence Packets 进行条件检查后的结果。

它是 Decision Candidate 的直接输入之一。

示例：

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
      "explanation": "行业供给收缩迹象存在，但需求端仍不明确。",
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
      "explanation": "核心财务质量指标未出现恶化。",
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
      "explanation": "估值处于历史较高分位，安全边际不足。",
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

### 16.1 impact_on_decision 枚举

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

### 16.2 overall_result 枚举

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

### 16.3 Constraint 聚合为 recommended_decision_bounds 的 MVP 规则

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
| block_strong_buy | 移除 strong_buy；MVP 中等价于禁止高置信度买入表达 |
| block_strong_sell | 移除 strong_sell |
| block_new_position | 移除 buy |
| block_add_position | 移除 add_position；MVP 中可映射为禁止加仓表达 |
| require_human_review | 标记 requires_human_review = true |
| need_more_data | 若涉及关键 Hard Constraint，则 overall_result = need_more_data |

#### 聚合规则

1. 从默认动作集合开始；
2. 按每个 Constraint 的 `impact_on_decision` 移除不允许动作；
3. 如果任一关键 Hard Constraint 返回 `need_more_data`，则整体 `overall_result = need_more_data`；
4. 如果多数关键 Hard Constraint fail，则整体 `overall_result = not_suitable_for_playbook`；
5. 如果存在 `require_human_review`，则整体标记 `requires_human_review = true`；
6. 最终剩余动作集合写入 `recommended_decision_bounds`。

示例：

```json
{
  "condition_impacts": [
    "support",
    "caution",
    "block_new_position"
  ],
  "recommended_decision_bounds": [
    "wait",
    "add_to_watchlist",
    "hold_if_already_owned"
  ],
  "overall_result": "not_passed_for_new_buy"
}
```

### 16.4 Playbook 全条件失败处理路径

当满足以下任一条件时，视为 Playbook 全条件失败或近似全条件失败：

1. 所有 Hard Constraints 均为 fail；
2. Hard Constraints 中超过 70% 为 fail，且无关键支持证据；
3. 所有关键条件状态为 fail 或 insufficient_data；
4. Playbook 的核心适用条件不成立。

系统不应强行生成普通 Decision Candidate。

应输出：

```text
not_suitable_for_playbook
```

或：

```text
need_more_data
```

当 `overall_result = not_suitable_for_playbook` 时：

1. 不生成 buy、add_position、strong_buy；
2. 可以生成 avoid_under_this_playbook；
3. 可以生成 add_to_watchlist，但必须说明不是当前 Playbook 下的可投资标的；
4. 必须在 Decision Trace 中展示失败条件；
5. 可以提示用户选择其他 Playbook 重新分析。

---

## 17. Guardrail Report 与 Resolved Decision Bounds

### 17.1 Guardrail Report

Guardrail Report 是系统边界检查结果。

MVP 阶段 Guardrails 至少包括：

1. 不承诺收益；
2. 不输出无依据强买入；
3. 数据不足时必须标记；
4. 模型预测不得表述为确定事实；
5. 不自动下单；
6. 高风险结论必须降级；
7. 反方证据缺失时不得输出强结论；
8. Playbook Hard Constraint 未通过时不得输出强建议。

示例：

```json
{
  "guardrail_report_id": "gr_001",
  "task_id": "task_001",
  "triggered": true,
  "findings": [
    {
      "guardrail_id": "gr_no_strong_buy_without_evidence",
      "severity": "medium",
      "description": "估值安全边际不足，不允许输出强买入建议。",
      "action": "downgrade_decision_bounds"
    }
  ],
  "overall_status": "passed_with_constraints"
}
```

### 17.2 Guardrail 与 Playbook Evaluation 的优先级

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

中文表达：

```text
护栏高于验证阻塞；
验证阻塞高于 Playbook 建议边界；
Playbook 边界高于冲突降级；
冲突降级高于风格偏好。
```

如果 Guardrail Report 触发 Block 级结果，则可以覆盖 Playbook Evaluation Report 中的 `recommended_decision_bounds`。

### 17.3 非 Block Guardrail 的降级语义

如果 Guardrail 不是 Block，但包含 `downgrade_decision_bounds`，则应影响 Resolved Decision Bounds。

示例：

```json
{
  "guardrail_report_id": "gr_001",
  "findings": [
    {
      "severity": "medium",
      "action": "downgrade_decision_bounds",
      "description": "数据质量不足，不允许输出 buy 类建议。"
    }
  ]
}
```

处理规则：

1. 从 `allowed_actions` 中移除强建议动作，例如 buy、strong_buy、add_position；
2. 保留谨慎动作，例如 wait、add_to_watchlist、hold_if_already_owned；
3. 降低 `confidence_cap`；
4. 在 Decision Trace 中展示 Guardrail 降级原因。

完整 Guardrail action 语义由 SPEC-009 定义。

### 17.4 Resolved Decision Bounds

Resolved Decision Bounds 用于合并来自 Validation、Conflict、Playbook Evaluation 和 Guardrail 的约束。

输入：

```text
Validation Reports
Conflict Reports
Playbook Evaluation Report
Guardrail Report
```

输出：

```text
Resolved Decision Bounds
```

示例：

```json
{
  "resolved_decision_bounds_id": "rdb_001",
  "allowed_actions": [
    "wait",
    "add_to_watchlist"
  ],
  "blocked_actions": [
    "buy",
    "strong_buy",
    "add_position"
  ],
  "requires_human_review": false,
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
  ],
  "reasoning": [
    "估值安全边际不足，Playbook 禁止新开仓",
    "Sentiment 数据质量低，降低置信度",
    "无 Guardrail Block"
  ]
}
```

MVP 阶段不要求复杂置信度传播模型，但必须满足：

1. `confidence_cap` 不得由 LLM 随机生成；
2. 每一次 confidence 降级必须有来源；
3. 最终 Decision Candidate 的 `confidence` 不得高于 `confidence_cap`；
4. 完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

Decision Candidate 只能从 `allowed_actions` 中选择 `suggested_action`。

### 17.5 后置 Guardrail 说明

v0.3.1 中 Guardrail 可以在 Decision Candidate 生成前后均可接入。

MVP 阶段只强制实现前置 Guardrail。

后置 Guardrail 可以留作后续版本，用于检查最终用户可见表达是否越界，例如：

1. 是否承诺收益；
2. 是否出现无依据强建议；
3. 是否隐藏反方证据；
4. 是否把模型预测表述为确定事实。

后置 Guardrail 的完整机制由 SPEC-009 定义。

---

## 18. Decision Candidate

Decision Candidate 是系统生成的投资判断候选。

它不是最终用户决策，而是系统在某个 Playbook 下给出的建议。

示例：

```json
{
  "candidate_id": "decision_001",
  "task_id": "task_001",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_evaluation_report_id": "pbe_001",
  "guardrail_report_id": "gr_001",
  "resolved_decision_bounds_id": "rdb_001",
  "validation_report_refs": [
    "val_post_card_001",
    "val_pre_decision_001"
  ],
  "conflict_report_refs": [
    "conflict_001"
  ],
  "suggested_action": "wait",
  "action_selection_reason": "Playbook Evaluation 禁止新开仓，Guardrail 禁止强买入，因此从 allowed_actions 中选择 wait。",
  "summary": "基本面和技术面支持关注，但估值偏高且情绪过热，不建议追高。",
  "confidence": 0.62,
  "supporting_points": [
    "基本面仍偏正面",
    "中期趋势未破坏"
  ],
  "blocking_points": [
    "估值处于高分位",
    "短期情绪过热"
  ],
  "next_checkpoints": [
    "下一次财报",
    "50 日均线",
    "毛利率趋势"
  ],
  "invalidating_conditions": [
    "收入增速明显低于预期",
    "跌破中期趋势线",
    "宏观流动性进一步收紧"
  ],
  "requires_human_review": false
}
```

任何 Decision Candidate 都必须能追溯到：

1. Analysis Cards；
2. Validation Reports；
3. Conflict Reports；
4. Playbook Evaluation Report；
5. Guardrail Report；
6. Resolved Decision Bounds；
7. Evidence Packets。

---

## 19. 系统状态与建议动作的语义分离

`analysis_incomplete` 和 `need_more_data` 不应混用。

### 19.1 系统状态

系统状态表示工作流是否完成。

建议字段：

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

### 19.2 建议动作

建议动作表示对用户的投资研究建议。

字段：

```json
{
  "suggested_action": "need_more_data"
}
```

`need_more_data` 只能作为用户可见建议动作，表示：

```text
建议用户补充更多数据后再判断。
```

### 19.3 规则

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

### 20.1 Workflow 名称

```text
single_stock_standard_analysis_workflow
```

### 20.2 Workflow 步骤

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

## 21. Playbook 在工作流中的介入点

Investment Playbook 不只在最后一步使用。

它应在三个阶段介入。

### 21.1 前置介入

在任务解析和工作流选择阶段，Playbook 影响：

1. 需要运行哪些能力域；
2. 哪些能力域更重要；
3. 分析时间周期；
4. 是否需要特定数据；
5. 是否需要特定风险检查。

### 21.2 中置介入

在能力域执行阶段，Playbook 影响：

1. 每个能力域必须检查哪些问题；
2. Analysis Card 必须输出哪些字段；
3. 哪些证据必须被引用；
4. 哪些反方证据必须出现。

### 21.3 后置介入

在最终建议生成阶段，Playbook 影响：

1. 条件通过 / 不通过；
2. 是否允许强建议；
3. 是否需要降级；
4. 是否进入观察列表；
5. 是否触发人工复核。

MVP 阶段 Playbook 的执行机制可以是结构化规则 + LLM 解释组合，但 Hard Constraint 必须由确定性逻辑执行。

完整机制由 SPEC-006 定义。

---

## 22. Playbook Lifecycle 概述

Playbook 必须支持版本管理。

### 22.1 Playbook 基本元数据

```json
{
  "playbook_id": "capital_cycle_fundamental_playbook",
  "version": "0.1.0",
  "created_by": "system",
  "created_at": "2026-06-14T00:00:00Z",
  "updated_at": "2026-06-14T00:00:00Z",
  "status": "active",
  "description": "面向资本周期和中长期基本面投资者的默认投资手册"
}
```

### 22.2 版本管理原则

1. 每次 Decision Trace 必须记录 playbook_id 和 playbook_version；
2. Playbook 变更后，历史 Decision Trace 仍应引用旧版本；
3. 同一任务使用不同 Playbook 得到不同结论时，系统应说明差异来自决策手册不同；
4. MVP 阶段可以不支持用户自由编辑 Playbook，但必须记录默认 Playbook 版本；
5. Playbook 的完整生命周期由 SPEC-006 定义。

### 22.3 Playbook 历史版本存储的 MVP 简化

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

完整 Playbook 历史版本管理由 SPEC-006 定义。

### 22.4 默认 Playbook 声明

MVP 默认 Playbook 为：

```text
capital_cycle_fundamental_playbook
```

该 Playbook 的完整结构由 SPEC-006 定义。

MVP 阶段可以使用内置静态版本。

要求：

1. 必须有 `playbook_id`；
2. 必须有 `playbook_version`；
3. 必须有最小 Hard / Soft Constraint 列表；
4. 必须能生成 Playbook Evaluation Report；
5. 必须进入 Decision Trace。

### 22.5 Playbook 适用性风险

系统早期版本只判断资产是否符合指定 Playbook，不判断 Playbook 本身是否适合当前市场环境。

这是已知局限性。

未来需要 Playbook Applicability Evaluator，用于判断：

1. 当前市场 regime 是否适合该 Playbook；
2. Playbook 是否过严；
3. Playbook 是否过松；
4. 是否导致用户系统性错过机会；
5. 是否需要提示用户复审 Playbook。

该能力不进入 MVP。

---

## 23. Review & Governance 接入点

### 23.1 Evaluator

MVP 阶段 Evaluator 是检查器，不是自动优化器。

它不自动重写分析结果，只标注问题。

Evaluator 输出必须被 Orchestrator 消费。

### 23.2 Guardrail Checker

MVP 阶段只强制实现前置 Guardrail。

前置 Guardrail 用于阻止明显不合规或不可靠路径。

后置 Guardrail 留作后续版本，用于检查最终用户可见表达是否越界。

### 23.3 Human-in-the-loop

MVP 阶段不强制实现完整人工审批流，但应预留状态。

以下场景可标记为需要人工复核：

1. 数据源冲突；
2. 重大突发事件；
3. 结论强烈但证据薄弱；
4. 用户持仓风险较高；
5. 模型置信度低；
6. Playbook 条件无法判断；
7. Guardrail 触发高风险标记；
8. High Conflict 触发。

状态字段：

```json
{
  "requires_human_review": true,
  "review_reason": "重大事件影响路径不明确"
}
```

---

## 24. 最小可用 Analysis Card 阈值

MVP 阶段不应在信息不足时强行生成 Decision Candidate。

### 24.1 Pre-decision Validation 阈值

Pre-decision Validation 负责检查：

1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals Card 必须可用；
3. 至少一个非 Fundamentals 的能力域提供有效支持或反方证据；
4. 至少没有 Block 级 Post-card Validation Finding；
5. 不存在未处理的 High Conflict。

### 24.2 Playbook Evaluation 阈值

Playbook Evaluation 负责检查：

1. Playbook 的关键 Hard Constraint 是否可以被判断；
2. 关键 Hard Constraint 是否通过；
3. 是否需要返回 `overall_result = need_more_data`；
4. 是否需要返回 `overall_result = requires_human_review`。

### 24.3 未达到阈值时

如果未达到 Pre-decision Validation 阈值，系统应输出：

```text
analysis_incomplete
```

而不是生成完整 Decision Candidate。

### 24.4 可例外场景

如果用户明确要求某一类专项分析，例如：

1. 只看技术面；
2. 只看财报；
3. 只解释事件；
4. 只做宏观背景分析；

则不要求满足 3/5 阈值，但输出类型必须是专项分析，不是完整 Decision Candidate。

---

## 25. 数据新鲜度与时效性策略

Context Bundle 和 Evidence Packet 必须支持数据新鲜度标记。

不同数据类型具有不同的有效期。

### 25.1 数据时间属性

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

### 25.2 数据新鲜度分级

建议分为：

1. real_time：实时或准实时，如价格、成交量；
2. intraday：日内有效，如技术指标；
3. daily：每日更新，如新闻摘要、情绪热度；
4. quarterly：季度更新，如财务报表；
5. event_based：事件触发更新，如公告、监管、诉讼；
6. static：低频变化，如公司行业分类。

### 25.3 重新运行策略

当用户连续分析同一标的时，系统应根据数据类型决定是否复用缓存。

MVP 阶段可以采用简单策略：

1. real_time / intraday 数据默认重新拉取；
2. daily 数据当天可复用；
3. quarterly 数据在新财报前可复用；
4. event_based 数据需要检查是否有新增事件；
5. static 数据可长期复用。

Decision Trace 必须显示关键数据的 as_of 时间。

---

## 26. Observability 与 Decision Trace 的数据关系

系统底层维护统一 Event Log。

Event Log 是 Observability 和 Decision Trace 的共同底层数据源。

MVP 阶段 Event Log 至少包含以下字段：

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
  "warnings": []
}
```

MVP 阶段支持以下 event_type：

1. run_started；
2. run_completed；
3. node_started；
4. node_completed；
5. node_failed；
6. model_called；
7. tool_called；
8. evidence_created；
9. analysis_card_created；
10. validation_finding_created；
11. conflict_created；
12. guardrail_triggered；
13. decision_candidate_created；
14. user_feedback_recorded。

三者关系：

```text
Event Log → Decision Trace
Event Log → Observability
```

Decision Trace 不应直接暴露全部 Event Log，而应筛选与投资判断相关的信息。

---

## 27. Macro / Meso MVP 实现层级

Macro / Meso 在 MVP 中保留为一级能力域，但不做完整宏观研究系统。

### 27.1 MVP 范围

MVP 阶段 Macro / Meso 只提供三个层级的信息：

1. Market Regime Context；
2. Industry / Capex Cycle Context；
3. Rate / Liquidity / Policy Context。

### 27.2 实现原则

MVP 阶段优先使用：

1. 外部数据源已有指标；
2. 人工维护或半结构化标签；
3. 简单规则模型；
4. 明确来源的政策或行业信息；
5. 少量 Agentic 解释。

MVP 阶段不做：

1. 自主宏观预测；
2. 复杂 regime 推断；
3. 完整行业供需模型；
4. 宏观资产配置模型；
5. 隐含宏观因子回归。

### 27.3 Macro / Meso partial 状态说明

Macro / Meso 在 MVP 中可能由于数据覆盖不足或能力降级，默认返回：

```text
domain_status = partial
```

这表示：

1. 该能力域输出可用于背景解释、风险提示或辅助判断；
2. 不应作为强建议的主要依据；
3. 不应单独触发 buy / sell；
4. 必须在 Decision Trace 中标记降权原因。

---

## 28. Sentiment MVP 降权策略

Sentiment 在 MVP 中保留为一级能力域，但默认视为高噪声能力域。

### 28.1 数据质量处理

如果 Sentiment Sources 数据质量为 low，则 Sentiment Card 仍可生成，但必须：

1. 标记低数据质量；
2. 降低默认置信度；
3. 不作为强建议的主要依据；
4. 不允许单独触发 buy / sell；
5. 主要用于风险提示、过热提示和叙事观察。

### 28.2 Sentiment 的默认角色

MVP 阶段 Sentiment 更适合回答：

1. 市场是否过热；
2. 是否存在恐慌；
3. 是否存在叙事拥挤；
4. 是否与基本面或事件出现背离；
5. 是否需要用户谨慎追高或谨慎抄底。

Sentiment 不应在 MVP 中承担核心定价判断。

### 28.3 Sentiment partial 状态说明

当 `data_quality = low` 时，Sentiment Card 默认应使用：

```json
{
  "domain_status": "partial",
  "data_quality": "low"
}
```

这不表示能力域失败，而表示该能力域输出只能用于风险提示和辅助判断。

---

## 29. MVP 架构边界

### 29.1 MVP 应实现

MVP 应实现：

1. 单股票标准分析 Workflow；
2. Investment Task 解析；
3. 默认 Investment Playbook；
4. Context Bundle 构建；
5. Evidence Packet 生成；
6. 五个分析能力域返回 Analysis Card；
7. Post-card Validation Report；
8. Conflict Report；
9. Pre-decision Validation Report；
10. Playbook Evaluation Report；
11. Guardrail Report；
12. Resolved Decision Bounds；
13. Decision Candidate；
14. Decision Trace Level 1 和 Level 2；
15. 基础 Event Log；
16. 数据时效性标记；
17. 最小 Analysis Card 阈值判断；
18. Metric Registry 静态映射表。

### 29.2 MVP 暂不实现

MVP 暂不实现：

1. 用户自由编辑复杂 Playbook；
2. 多股票批量扫描；
3. 组合优化；
4. 自动交易；
5. 实盘订单接入；
6. Bull/Bear 多 Agent 辩论；
7. Evaluator 自动重写；
8. 完整 Observability Dashboard；
9. 完整 Case Library；
10. Playbook Applicability Evaluator；
11. 复杂宏观预测系统；
12. 完整行业供需模型；
13. 完整置信度传播模型；
14. 后置 Guardrail 完整机制。

### 29.3 MVP 默认用户定位

MVP 优先面向：

1. 资本周期投资者；
2. 产业周期投资者；
3. 中长期基本面投资者；
4. 价值与成长结合型投资者；
5. 关注宏观/中观与公司基本面关系的主动投资者。

---

## 30. 错误与降级策略

### 30.1 数据缺失

如果某类数据缺失，系统不应中断整个工作流。

对应能力域应返回：

```text
insufficient_data
```

并说明：

1. 缺失数据；
2. 影响范围；
3. 是否影响最终建议；
4. 用户下一步应补充什么。

### 30.2 能力域失败

如果某个能力域执行失败，编排器应：

1. 记录错误；
2. 标记该能力域不可用；
3. 继续执行其他能力域；
4. 在 Decision Trace 中展示缺失影响；
5. 降低最终结论置信度。

### 30.3 证据冲突

如果证据冲突，系统不应自动消除。

应生成 Conflict Report，并在最终建议中说明冲突如何影响判断。

### 30.4 Guardrail 触发

如果 Guardrail 触发严重风险，系统应：

1. 降级最终建议；
2. 要求更多数据；
3. 提醒用户人工复核；
4. 避免强建议表达。

### 30.5 未达到最小卡片阈值

如果未达到最小可用 Analysis Card 阈值，系统应：

1. 不生成完整 Decision Candidate；
2. 输出 `analysis_incomplete`；
3. 展示缺失能力域；
4. 提示用户是否转为专项分析。

### 30.6 Playbook 不适配

如果 Playbook Evaluation Report 返回 `not_suitable_for_playbook`，系统应：

1. 不生成普通买入建议；
2. 输出“不符合当前 Playbook”的专项判断；
3. 可以建议用户更换 Playbook；
4. 在 Decision Trace 中展示失败条件。

---

## 31. Run State

每次工作流运行应维护 Run State。

Run State 至少包含：

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

MVP 阶段 Run State 中 `playbook_evaluation_report` 保持单值，因为 MVP 只支持单一 Playbook 执行路径。

未来如果支持多 Playbook 对比，应改为：

```json
{
  "playbook_evaluation_reports": []
}
```

并在 Decision Candidate 中明确绑定使用哪一个 Playbook Evaluation Report。

---

## 32. 后续 SPEC 依赖

### SPEC-004：五类分析能力域与 Analysis Card Schema

负责定义：

1. 每个能力域内部输入；
2. 每个能力域输出字段；
3. 每个能力域质量标准；
4. Analysis Card 完整 schema；
5. 每个能力域如何区分 Computed / Structured / Interpreted Evidence；
6. 每个能力域如何输出可被 Playbook Constraint 引用的 metrics 或 facts。

### SPEC-005：Capability Package 与 Metric Registry 规范

负责定义：

1. Capability Package 结构；
2. 工具、模型、Skill、Evaluator 的封装方式；
3. Metric Registry 完整 schema；
4. metric:// 引用解析机制。

### SPEC-006：Investment Playbook 规范

负责定义：

1. Playbook 结构；
2. Playbook 执行机制；
3. Hard / Soft Constraint 规则；
4. Constraint 结果聚合规则的完整版本；
5. Playbook 生命周期；
6. Playbook 与 Workflow 的关系；
7. 置信度传播最小规则或完整模型。

### SPEC-007：Orchestration 与执行路径

负责定义：

1. 更多 Workflow 类型；
2. Routing 规则；
3. 多 Agent Debate；
4. Human-in-the-loop；
5. 失败重试与恢复；
6. 多股票和组合层执行路径。

### SPEC-008：Decision Trace 与 Observability

负责定义：

1. Event Log 完整 schema；
2. Decision Trace 展示层级；
3. Observability 视图；
4. 用户复盘记录。

### SPEC-009：Governance、Guardrails、Evaluator 与人工介入

负责定义：

1. Guardrail 规则；
2. Evaluator 检查项；
3. 人工复核条件；
4. 合规边界；
5. Block / Flag / Note 的完整处理规则；
6. 后置 Guardrail 机制。

### SPEC-011：Case Library 与历史案例记忆

负责定义：

1. Case Card 结构；
2. 案例适用条件；
3. 案例与 Playbook 的关系；
4. 案例如何进入 Decision Trace；
5. 案例如何避免路径依赖。

### SPEC-012：数据治理与用户私有数据

负责定义：

1. 用户持仓数据；
2. 用户历史分析记录；
3. 用户 Playbook；
4. 用户反馈；
5. 用户复盘笔记；
6. 私有数据权限和删除机制。

---

## 33. 开放问题

### 33.1 Playbook 执行机制

MVP 阶段 Playbook 可采用结构化规则 + LLM 解释组合。

但长期需要明确：

1. 哪些规则必须结构化；
2. 哪些判断允许 LLM 解释；
3. 哪些条件触发 Guardrail；
4. 如何测试 Playbook 是否被正确执行；
5. 如何支持用户自定义 Playbook。

### 33.2 Playbook 适用性评估

当前架构只判断资产是否符合指定 Playbook。

未来需要判断：

1. Playbook 是否适合当前市场 regime；
2. Playbook 是否过严；
3. Playbook 是否过松；
4. Playbook 是否导致系统性错过机会。

该能力不进入 MVP。

### 33.3 多股票与组合层扩展

当前架构以单股票分析为中心。

未来需要扩展到：

1. 股票池初筛；
2. 多股票横向比较；
3. 组合风险暴露；
4. 仓位建议；
5. 组合层 Decision Trace。

### 33.4 用户私有数据接入

如果使用用户持仓、交易记录、历史分析或复盘笔记，需要独立数据治理机制。

相关内容由 SPEC-012 定义。

### 33.5 Evidence 可靠性与投资重要性的权衡

Computed Evidence 更可靠，但不一定更重要。

Interpreted Evidence 不够确定，但在某些重大事件中可能具有很高投资重要性。

未来需要定义：

1. 可靠性评分；
2. 投资重要性评分；
3. 两者如何共同影响 Decision Candidate。

---

## 34. SPEC-003 v0.3.1 总结

crosslens 的 Agentic 投研工作流架构应以 Orchestrator 和状态化 Workflow 为核心。

系统不应是多 Agent 群聊，也不应是黑箱买卖信号生成器。

推荐架构是：

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

MVP 阶段应优先实现：

```text
单股票标准分析 Workflow
+ 五个 Analysis Card
+ 默认 Investment Playbook
+ Evidence Packet 三级分类
+ Post-card / Pre-decision Validation
+ Conflict Detection
+ Playbook Evaluation
+ Guardrail Check
+ Resolved Decision Bounds
+ Decision Candidate
+ Decision Trace
+ Metric Registry 静态映射表
```

v0.3.1 的核心目标是让 SPEC-003 更接近 MVP 可实现状态。

本版本补齐：

1. Pre-decision Validation 与 Playbook Evaluation 的职责边界；
2. `confidence_cap` 来源记录；
3. Post-card Validation Block 后的 Card 过滤逻辑；
4. 非 Block Guardrail 的降级语义；
5. Hard Constraint 确定性表述修正；
6. Metric Registry 的 MVP 最小形态；
7. `recommended_decision_bounds` 的聚合规则；
8. `facts` 与 `metrics` 的字段区分；
9. 后置 Guardrail 的 MVP 边界；
10. 单 Playbook Evaluation Report 的 MVP 假设；
11. Macro / Meso 与 Sentiment 的 partial 状态语义。

crosslens SPEC-003 v0.3.1 继续坚持架构宪法：

```text
Deterministic first, Agentic when necessary, Traceable always.
```

---

文档结束 | 版本 v0.3.1 | 项目 crosslens
