# SPEC-003：Agentic 投研工作流架构

**版本：** v0.2.1  
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
5. Evidence Packet、Analysis Card、Decision Candidate、Decision Trace 如何流转；
6. Investment Playbook 在工作流中如何介入；
7. Evaluator、Guardrail、Human-in-the-loop 在哪里介入；
8. MVP 阶段的标准单股票分析流程是什么。

本 SPEC 不详细定义：

1. 五个分析能力域内部实现；
2. 每个能力域使用哪些具体模型、工具或 Agent；
3. Investment Playbook 的完整结构和执行机制；
4. Decision Trace 的完整 UI 展示方式；
5. Case Library 的结构；
6. 数据治理和用户私有数据权限。

以上内容分别由后续 SPEC 定义。

### v0.2 修订目标

SPEC-003 v0.2 的目标是加固 v0.1 中尚未闭合的关键架构关节，避免系统在实现时滑向"LLM 生成证据、LLM 判断规则、LLM 自我审查"的不确定路径。本次修订重点处理：

1. Validation Report 和 Playbook Evaluation Report 缺少正式对象定义；
2. Evidence Packet 的生成机制未区分确定性、结构化模型和 Agentic 推理；
3. Playbook 条件判断机制存在不确定性风险；
4. Evaluator 标注后缺少处理闭环；
5. Conflict Report 对 Decision Candidate 的影响机制不明确；
6. Event Log 缺少 MVP 最小字段；
7. 数据时效性策略缺失；
8. Macro/Meso 与 Sentiment 在 MVP 中的能力边界需要操作化；
9. 最小可用 Analysis Card 阈值缺失；
10. Playbook 生命周期与版本管理缺失。

---

## 2. 架构核心判断

crosslens 不应被设计为一个"多 Agent 群聊系统"。

crosslens 的核心架构应是：**可控的状态化投研 Workflow，必要节点引入 Agentic Reasoning，并对全过程进行审计和复盘。**

也就是说：

1. 外层：Workflow / State Machine / Orchestrator
2. 内层：Models / Tools / Agents / Evaluators
3. 结果：Analysis Cards + Decision Candidate + Decision Trace

系统不应让一个超级 Agent 自由决定全部流程，也不应把所有步骤都写死为不可变流水线。

推荐范式：

- **Workflow first, Agent when needed.**
- **Evidence before reasoning.**
- **State machine outside, agentic reasoning inside.**
- **Every decision must produce a trace.**

中文表达：

- 优先工作流，必要时才使用 Agent；
- 先生成证据，再进行推理；
- 外层状态机可控，内层允许 Agentic 推理；
- 每次建议都必须生成决策链。

### v0.2 架构原则升级

v0.2 进一步将架构原则落实为：

> **Deterministic first, Agentic when necessary, Traceable always.**

**该原则是 crosslens 工作流架构的宪法性约束。**

即：

1. Evidence Packet 必须标记生成机制（Computed / Structured / Interpreted）
2. Computed Evidence 优先于 Structured Evidence，Structured Evidence 优先于 Interpreted Evidence
3. Playbook 的硬性条件必须由规则引擎或确定性逻辑执行
4. LLM 可以解释 Playbook 条件，但不能替代硬性条件判断
5. Evaluator 标注必须进入 Block / Flag / Note 处理路径
6. Conflict Report 必须影响 Decision Candidate 的建议边界
7. 未达到最小 Analysis Card 阈值时，不生成完整 Decision Candidate
8. 每一步的生成机制、数据来源和确定性等级必须可追溯

---

## 3. 设计原则

### 3.1 编排器不侵入能力域内部实现

编排器调度全局 Workflow 节点和能力域级 Analysis Domain Job。

编排器不直接调度能力域内部的模型、工具、Agent 或子 Workflow。

能力域内部如何组合模型、工具、Workflow、Agent、Evaluator，由该能力域自行定义。

编排器只依赖能力域暴露的标准接口：

**Input:**
- Investment Task
- Context Bundle
- Playbook Constraints
- Run Config

**Output:**
- Analysis Card
- Domain Event Log
- Error / Warning / Data Quality Flags

### 3.2 能用确定性流程解决的，不强行使用 Agent

例如：
- 技术指标计算；
- 财务比率计算；
- 估值分位计算；
- 数据校验；
- Playbook 硬性条件检查。

这些优先由工具、模型或规则完成。

Agent 主要用于：
- 开放式解释；
- 事件影响路径分析；
- 冲突归因；
- 反方观点生成；
- 不确定性表达；
- 用户问题追问；
- 投资语境化解释。

### 3.3 证据对象优先于长文本分析

系统应先生成结构化 Evidence Packet，再由能力域生成 Analysis Card。

Agent 不应直接基于模糊上下文自由分析，而应基于明确证据进行解释。

**v0.2 增加要求**：Evidence Packet 必须标记生成机制类型（详见第 7 节）。Computed Evidence 优先于 Structured Evidence，Structured Evidence 优先于 Interpreted Evidence。

### 3.4 冲突应该被暴露，而不是被平均

如果不同能力域结论冲突，系统不应强行压成一个综合分数。

例如：
- 基本面正面，但估值过高；
- 技术面趋势良好，但情绪过热；
- 宏观环境压制估值，但公司事件催化强。

这些冲突应进入 Conflict Detection，并在 Decision Trace 中展示。

**v0.2 增加要求**：冲突必须影响 Decision Candidate 的建议边界（详见第 13 节）。

### 3.5 Playbook 约束判断，不替代证据

Investment Playbook 表达用户或系统的投资风格和决策偏好。

Playbook 不应替代事实和证据生成，而应在三个阶段发挥作用：
1. 前置：影响分析重点；
2. 中置：约束 Analysis Card 的检查项；
3. 后置：参与 Decision Candidate 生成。

**v0.2 增加要求**：Playbook 的硬性条件（Hard Constraint）必须由规则引擎或确定性逻辑执行，不得由 LLM 直接判断。

### 3.6 用户保留最终控制权

系统可以生成投资判断建议，但不替代用户做最终投资决策。

MVP 阶段不做自动下单，不做收益承诺，不做黑箱荐股。

---

## 4. 总体架构

crosslens 的 Agentic 投研工作流采用七层架构：

1. User Interaction Layer
2. Task Understanding & Routing Layer
3. Context & Evidence Layer
4. Orchestration Layer
5. Execution Layer
6. Review & Governance Layer
7. Decision & Trace Layer

### 4.1 七层关系

```
User Request
  ↓
User Interaction Layer
  ↓
Task Understanding & Routing Layer
  ↓
Orchestration Layer
  ↓
Context & Evidence Layer
  ↓
Execution Layer
  ↓
Review & Governance Layer
  ↓
Decision & Trace Layer
  ↓
User Review / Feedback / Save for Replay
```

需要注意：
- Orchestration Layer 是系统中枢；
- Context & Evidence Layer 负责生成可验证证据；
- Execution Layer 负责调用能力域；
- Review & Governance Layer 负责质量检查和边界控制；
- Decision & Trace Layer 负责用户可理解的结论和证据链展示。

---

## 5. 核心对象定义

### 5.1 Investment Task

Investment Task 是系统对用户请求的标准化表达。

用户输入可能是自然语言，例如：**帮我看看现在能不能买入 NVDA，按成长股中期持有逻辑。**

系统应将其解析为结构化任务：

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
  "playbook_id": "growth_mid_term",
  "depth": "standard",
  "risk_preference": "medium",
  "created_at": "2026-06-14T00:00:00Z"
}
```

Investment Task 至少包含：
1. 任务类型；
2. 资产标识；
3. 用户意图；
4. 时间周期；
5. 投资风格或 Playbook；
6. 分析深度；
7. 风险偏好；
8. 是否涉及用户私有数据；
9. 任务创建时间。

### 5.2 Context Bundle

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

示例：

```json
{
  "task_id": "task_001",
  "asset": "NVDA",
  "as_of": "2026-06-14",
  "contexts": {
    "market_data": "...",
    "financials": "...",
    "company_events": "...",
    "sentiment_sources": "...",
    "macro_meso_brief": "...",
    "user_private_context": null
  },
  "data_quality": {
    "market_data": "high",
    "financials": "medium",
    "sentiment_sources": "low"
  }
}
```

Context Bundle 不等于最终证据。它是生成 Evidence Packet 的原材料。

**v0.2 增加要求**：Context Bundle 必须支持数据新鲜度标记（详见第 8 节）。

### 5.3 Evidence Packet

Evidence Packet 是模型、工具或检索过程生成的结构化证据对象。

它用于把原始数据转换为可消费的事实、指标、分类、评分或异常提示。

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
  "generation_mechanism": "computed",
  "facts": [
    "price_above_50d_ma",
    "rsi_68",
    "volume_1.4x_20d_average"
  ],
  "signal": "positive",
  "confidence": 0.72,
  "data_quality": "high",
  "time_horizon": "2-6 weeks",
  "freshness_level": "intraday",
  "can_support_hard_constraint": true,
  "limitations": [
    "technical signal may fail around earnings event"
  ]
}
```

Evidence Packet **v0.2** 至少包含：
1. 证据 ID；
2. 任务 ID；
3. 所属能力域；
4. 来源类型；
5. 来源名称；
6. 时间戳；
7. 证据类型；
8. **生成机制（generation_mechanism：computed / structured / interpreted）**；
9. 事实或结果；
10. 信号方向；
11. 置信度；
12. 数据质量；
13. **数据新鲜度等级（freshness_level）**；
14. 适用时间周期；
15. **可否支撑硬性条件（can_support_hard_constraint）**；
16. 局限性。

**Evidence Packet 生成机制分类详见第 7 节。**

### 5.4 Analysis Domain Job

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
      {
        "constraint_id": "growth_001",
        "name": "收入增速高于行业中位数",
        "condition_type": "hard",
        "input_refs": ["revenue_growth", "industry_median_revenue_growth"],
        "operator": ">",
        "threshold_ref": "industry_median_revenue_growth",
        "priority": "high",
        "on_fail": "block_strong_buy",
        "on_insufficient_data": "flag"
      }
    ]
  },
  "run_config": {
    "depth": "standard",
    "allow_agent_reasoning": true,
    "require_opposing_evidence": true
  }
}
```

**v0.2 改动**：`playbook_constraints` 从字符串列表升级为结构化约束，包含操作符、阈值引用、失败处理和优先级。约束结构详见第 6 节。

Analysis Domain Job 是编排器与能力域的接口边界。

### 5.5 Analysis Card

Analysis Card 是每个能力域向编排器返回的标准化分析结果。

示例：

```json
{
  "card_id": "card_fundamentals_001",
  "task_id": "task_001",
  "domain": "fundamentals",
  "summary": "基本面偏正面，但估值压力较高",
  "stance": "moderately_positive",
  "confidence": 0.66,
  "time_horizon": "6-12 months",
  "supporting_evidence": [
    {
      "evidence_id": "ev_financial_001",
      "description": "收入增速高于行业中位数"
    },
    {
      "evidence_id": "ev_cashflow_001",
      "description": "自由现金流率改善"
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
    "下季度收入增速低于行业中位数",
    "自由现金流转负"
  ],
  "data_quality": "medium",
  "warnings": []
}
```

Analysis Card 至少包含：
1. 能力域名称；
2. 核心结论；
3. 立场方向；
4. 置信度；
5. 时间周期；
6. 支持证据；
7. 反方证据；
8. 关键风险；
9. 失效条件；
10. 数据质量；
11. 警告或异常。

Analysis Card 的完整 schema 由 SPEC-004 定义。

### 5.6 Conflict Report

Conflict Report 用于记录不同 Analysis Card 之间的冲突。

示例：

```json
{
  "conflict_id": "conflict_001",
  "task_id": "task_001",
  "conflict_type": "fundamentals_vs_sentiment",
  "severity": "medium",
  "description": "基本面偏正面，但情绪信号显示短期过热",
  "involved_cards": [
    "card_fundamentals_001",
    "card_sentiment_001"
  ],
  "decision_implication": "不适合追高，适合等待回调或观察财报确认"
}
```

Conflict Report 不用于消除冲突，而用于展示冲突。

**v0.2 增加要求**：Conflict severity 分为 low / medium / high。Conflict Report 必须影响 Decision Candidate 的建议边界（详见第 13 节）。

### 5.7 Decision Candidate

Decision Candidate 是系统生成的投资判断候选。

它不是最终用户决策，而是系统在某个 Playbook 下给出的建议。

示例：

```json
{
  "candidate_id": "decision_001",
  "task_id": "task_001",
  "playbook_id": "growth_mid_term",
  "suggested_action": "wait",
  "summary": "基本面和技术面支持关注，但估值偏高且情绪过热，不建议追高。",
  "confidence": 0.62,
  "suitable_for": "growth_mid_term",
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
  ]
}
```

常见建议动作可以包括：
1. buy；
2. hold；
3. wait；
4. avoid；
5. reduce；
6. add_to_watchlist；
7. need_more_data。

MVP 阶段建议避免使用过强的"buy / sell"语言，优先使用：
- 可关注；
- 加入观察；
- 等待确认；
- 不建议追高；
- 需要更多数据；
- 已有仓位可继续观察；
- 风险上升，建议复核。

### 5.8 Decision Trace

Decision Trace 是面向用户的投研证据链。

它回答：
1. 系统如何理解任务；
2. 选择了哪条执行路径；
3. 使用了哪些数据；
4. 生成了哪些 Evidence Packet；
5. 五个能力域分别给出什么 Analysis Card；
6. 哪些能力域之间存在冲突；
7. Playbook 哪些条件被触发；
8. Evaluator 标记了哪些问题；
9. Guardrails 是否触发；
10. 为什么生成当前 Decision Candidate；
11. 用户下一步应检查什么。

Decision Trace 不等同于 Observability。

Observability 面向开发和运维，Decision Trace 面向用户和投研复盘。

### 5.9 Validation Report **[v0.2 新增]**

Validation Report 是 Evaluator 对 Analysis Cards 或 Decision Candidate 的质量检查结果。

它不是 Analysis Card，也不是 Decision Trace，而是工作流中的质量控制对象。

#### 5.9.1 生成时机

Validation Report 可以在两个阶段生成：
1. Analysis Card 生成后；
2. Decision Candidate 生成前。

MVP 阶段优先实现第一种。

#### 5.9.2 示例结构

```json
{
  "validation_report_id": "val_001",
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
      "description": "Sentiment Card 缺少反方证据，未说明情绪信号可能失真的原因。",
      "recommended_handling": "lower_confidence"
    },
    {
      "finding_id": "finding_002",
      "severity": "note",
      "finding_type": "low_data_quality",
      "target_ref": "card_sentiment_001",
      "description": "情绪数据源质量较低，建议在 Decision Trace 中提示用户。",
      "recommended_handling": "show_in_trace"
    }
  ],
  "overall_status": "passed_with_flags"
}
```

`overall_status` 取值：`passed` / `passed_with_notes` / `passed_with_flags` / `blocked` / `failed`。

| overall_status | 含义 | 后续处理 |
|---|---|---|
| `passed` | 未发现问题 | 正常进入下一步 |
| `passed_with_notes` | 仅存在 Note 级问题 | 正常进入下一步，记录日志 |
| `passed_with_flags` | 存在 Flag 级问题，但无 Block | 继续执行，但降低置信度，并进入 Decision Trace |
| `blocked` | 存在 Block 级问题 | 不生成强 Decision Candidate，输出 `need_more_data` 或 `analysis_incomplete` |
| `failed` | Evaluator 自身执行失败 | 记录系统错误，允许工作流降级，但必须在 Decision Trace 中标记 |

#### 5.9.3 severity 分级

Validation Finding 必须分为三类：

**Block**
- 阻止继续生成强建议，或要求 Decision Candidate 降级。
- 适用情况：关键证据严重缺失；Guardrail 高风险触发；Analysis Card 存在明显无依据判断；必要能力域不可用；数据冲突严重且无法解释。

**Flag**
- 不阻止工作流继续，但必须降低置信度，并进入 Decision Trace。
- 适用情况：反方证据不足；数据质量较低；时间周期不清；置信度过高；模块冲突未充分解释。

**Note**
- 仅记录，不影响 Decision Candidate。
- 适用情况：格式轻微偏差；非关键字段缺失；低影响数据提示；可供复盘的信息。

#### 5.9.4 处理规则

MVP 阶段 Evaluator 不自动重写输出。但 Evaluator 的输出**必须被 Orchestrator 消费**：

| Severity | 处理 |
|----------|------|
| Block | 降级 Decision Candidate，或返回 need_more_data |
| Flag | 降低置信度，进入 Decision Trace |
| Note | 进入 Event Log，可选择性展示 |

MVP 阶段根据 `overall_status` 的处理：

- `passed`、`passed_with_notes`：正常执行；
- `passed_with_flags`：正常执行，但降低 Decision Candidate 置信度；
- `blocked`：不得生成强建议；
- `failed`：不得隐藏错误，必须展示为系统执行不完整。

**Evaluator 不应只是日志工具。**

### 5.10 Playbook Evaluation Report **[v0.2 新增]**

Playbook Evaluation Report 是系统根据 Investment Playbook 对 Analysis Cards、Conflict Reports 和 Evidence Packets 进行条件检查后的结果。

它是 Decision Candidate 的直接输入之一。

#### 5.10.1 示例结构

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
      "evidence_refs": ["ev_macro_001", "card_macro_001"],
      "explanation": "行业供给收缩迹象存在，但需求端仍不明确。",
      "impact_on_decision": "caution"
    },
    {
      "condition_id": "ccfp_002",
      "condition_name": "公司财务质量未恶化",
      "condition_type": "hard",
      "status": "pass",
      "evidence_refs": ["card_fundamentals_001"],
      "explanation": "核心财务质量指标未出现恶化。",
      "impact_on_decision": "support"
    },
    {
      "condition_id": "ccfp_003",
      "condition_name": "估值具有安全边际",
      "condition_type": "hard",
      "status": "fail",
      "evidence_refs": ["ev_valuation_001"],
      "explanation": "估值处于历史较高分位，安全边际不足。",
      "impact_on_decision": "block_strong_buy"
    }
  ],
  "blocking_conditions": ["估值安全边际不足"],
  "overall_result": "not_passed_for_new_buy",
  "recommended_decision_bounds": [
    "wait",
    "add_to_watchlist",
    "hold_if_already_owned"
  ]
}
```

#### 5.10.2 `impact_on_decision` 枚举 **[v0.2.1 新增]**

每个 Playbook Condition 必须包含 `impact_on_decision` 字段。

可选值：

| impact_on_decision | 含义 |
|---|---|
| `support` | 支持当前 Playbook 下的正向判断 |
| `neutral` | 对最终判断无明显方向性影响 |
| `caution` | 提醒谨慎，但不阻止建议生成 |
| `lower_confidence` | 降低最终建议置信度 |
| `block_strong_buy` | 禁止输出强买入类建议 |
| `block_strong_sell` | 禁止输出强卖出类建议 |
| `block_new_position` | 禁止建议新开仓 |
| `block_add_position` | 禁止建议加仓 |
| `require_human_review` | 标记需要人工复核 |
| `need_more_data` | 数据不足，无法判断该条件 |

`impact_on_decision` 不直接生成最终建议，只约束 Decision Candidate 的建议空间。

例如：`condition fail + impact_on_decision = block_new_position` 意味着系统可以输出 `add_to_watchlist` / `wait` / `hold_if_already_owned` / `need_more_data`，但不应输出 `buy` / `strong_buy` / `add_position`。

#### 5.10.3 Playbook Evaluation 的作用

Playbook Evaluation Report 不直接等于最终建议。它用于约束 Decision Candidate：
1. 哪些建议动作被允许；
2. 哪些建议动作被禁止；
3. 哪些条件导致建议降级；
4. 哪些条件需要人工复核；
5. 哪些不确定性需要进入 Decision Trace。

#### 5.10.4 `overall_result` 枚举 **[v0.2.1 扩展]**

| overall_result | 含义 | 推荐 Decision Candidate 边界 |
|---|---|---|
| `passed` | 主要条件通过 | 可生成正向建议，但仍需 Guardrail 检查 |
| `partially_passed` | 部分通过，存在阻塞或不确定项 | 优先输出 `wait` / `add_to_watchlist` / `hold_if_already_owned` |
| `not_passed_for_new_buy` | 不适合新开仓 | 不建议新买入，可继续观察 |
| `not_passed_for_add_position` | 不适合加仓 | 已持有可复核，禁止加仓建议 |
| `not_suitable_for_playbook` | 资产与当前 Playbook 明显不匹配 | 输出 Playbook 不适配说明，而非普通投资建议 |
| `need_more_data` | 关键条件无法判断 | 不生成完整 Decision Candidate |
| `requires_human_review` | 需要人工复核 | 不生成强建议 |

#### 5.10.5 Playbook 全条件失败处理路径 **[v0.2.1 新增]**

当满足以下任一条件时，视为 Playbook 全条件失败或近似全条件失败：

1. 所有 Hard Constraints 均为 `fail`；
2. Hard Constraints 中超过 70% 为 `fail`，且无关键支持证据；
3. 所有关键条件状态为 `fail` 或 `insufficient_data`；
4. Playbook 的核心适用条件不成立。

**处理结果**：系统不应强行生成普通 Decision Candidate。应输出 `not_suitable_for_playbook` 或 `need_more_data`。

**用户可见表达示例**：

> 按照当前的 capital_cycle_fundamental_playbook，该标的不适合进入完整投资判断流程。主要原因是：行业资本周期条件不成立、估值安全边际不足、公司基本面条件未通过。建议更换 Playbook、补充数据，或将本次输出视为"不符合当前投资手册"的专项判断，而不是买卖建议。

**系统行为**：当 `overall_result = not_suitable_for_playbook` 时：
1. 不生成 `buy`、`add_position`、`strong_buy`；
2. 可以生成 `avoid_under_this_playbook`；
3. 可以生成 `add_to_watchlist`，但必须说明不是当前 Playbook 下的可投资标的；
4. 必须在 Decision Trace 中展示失败条件；
5. 可以提示用户选择其他 Playbook 重新分析。

---

## 6. Playbook Constraint 结构化定义 **[v0.2 新增]**

v0.1 中 `playbook_constraints` 使用字符串列表表示，例如 `["check_revenue_growth", "check_margin_trend"]`。这只能作为占位，不足以支持机器可执行判断。

MVP 阶段应引入最小结构化格式。

### 6.1 示例结构

```json
{
  "constraint_id": "growth_001",
  "name": "收入增速高于行业中位数",
  "condition_type": "hard",
  "input_refs": ["revenue_growth", "industry_median_revenue_growth"],
  "operator": ">",
  "threshold_ref": "industry_median_revenue_growth",
  "priority": "high",
  "on_fail": "block_strong_buy",
  "on_insufficient_data": "flag"
}
```

### 6.2 条件类型

Playbook Constraint 至少分为两类：

#### Hard Constraint

**必须由规则引擎或确定性逻辑执行。** 不应由 LLM 直接判断。

适用对象：
- 数值阈值；
- 趋势方向；
- 存在性检查；
- 数据缺失检查；
- 仓位或风险硬限制；
- 明确禁止条件。

Hard Constraint 引用的数据源应优先来自 Computed Evidence 或高置信度 Structured Evidence。如果输入源本身置信度不足，Constraint 应降级为 Soft。

#### Soft Constraint

可以由 LLM 辅助解释，但必须保留证据引用。

适用对象：
- 事件影响路径；
- 宏观环境适配；
- 叙事是否过热；
- 管理层表述变化；
- 行业周期阶段判断。

Soft Constraint 的结果必须标记不确定性。

---

## 7. Evidence Packet 生成机制分类 **[v0.2 新增]**

Evidence Packet 不应默认由 LLM 生成。根据生成机制分为三类。

### 7.1 Computed Evidence

Computed Evidence 由确定性计算、规则或数据接口生成。

**特点**：可复现；可测试；可审计；不依赖 LLM 推理；优先级最高。

**示例**：
- 财务比率；
- 收入增速；
- 毛利率变化；
- 自由现金流率；
- PE / PB / EV/EBITDA 分位；
- RSI / MACD / ATR；
- 成交量放大倍数；
- 价格相对均线位置；
- 是否跌破关键均线；
- 数据是否缺失。

Computed Evidence 是 MVP 最优先支持的证据类型。

### 7.2 Structured Evidence

Structured Evidence 由专门模型、分类器、规则模型或半结构化抽取器生成。

**特点**：有明确输入输出；有置信度；可评估；可能有误差；需要记录模型版本。

**示例**：
- 公司事件分类；
- 情绪标签；
- 新闻主题分类；
- 宏观 regime 标签；
- 行业周期阶段；
- 风险事件识别；
- 财报语气变化；
- 管理层指引变化。

Structured Evidence 必须记录：模型名称；模型版本；置信度；数据来源；适用范围；局限性。

### 7.3 Interpreted Evidence

Interpreted Evidence 由 Agentic Reasoning 或 LLM 解释生成。

**特点**：不完全可复现；依赖上下文和模型；需要明确标记；不应作为硬性规则的唯一依据；必须进入 Decision Trace 的不确定性说明。

**示例**：
- 事件影响路径解释；
- 管理层意图推测；
- 地缘事件对行业的间接影响；
- 市场叙事变化；
- 情绪与基本面背离解释；
- 资本周期阶段的文字判断。

Interpreted Evidence 必须标记：
```json
{
  "determinism_level": "interpreted",
  "can_support_hard_constraint": false
}
```

### 7.4 证据优先级

当不同证据冲突时，默认优先级为：

> **Computed Evidence > Structured Evidence > Interpreted Evidence**

但这只是证据可靠性优先级，不等于投资重要性优先级。例如，一个重大政策事件的 Interpreted Evidence 可能投资重要性很高，但仍需标记为解释性判断。

---

## 8. 数据新鲜度与时效性策略 **[v0.2 新增]**

Context Bundle 和 Evidence Packet 必须支持数据新鲜度标记。

### 8.1 数据时间属性

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

### 8.2 数据新鲜度分级

| 等级 | 含义 | 示例 |
|------|------|------|
| `real_time` | 实时或准实时 | 价格、成交量 |
| `intraday` | 日内有效 | 技术指标 |
| `daily` | 每日更新 | 新闻摘要、情绪热度 |
| `quarterly` | 季度更新 | 财务报表 |
| `event_based` | 事件触发更新 | 公告、监管、诉讼 |
| `static` | 低频变化 | 公司行业分类 |

### 8.3 Evidence Packet 时效性

Evidence Packet 必须继承或声明自己的时效性。例如：
- RSI=68 → intraday；
- 最新季度毛利率 → quarterly；
- 公司产品召回事件 → event_based；
- Market Regime 标签 → daily 或 weekly；
- Reddit 情绪热度 → daily 或 intraday。

### 8.4 重新运行策略

当用户连续分析同一标的时，系统应根据数据类型决定是否复用缓存。

MVP 阶段可以采用简单策略：
- real_time / intraday 数据默认重新拉取；
- daily 数据当天可复用；
- quarterly 数据在新财报前可复用；
- event_based 数据需要检查是否有新增事件；
- static 数据可长期复用。

Decision Trace 必须显示关键数据的 as_of 时间。

---

## 9. 编排器调度模型

### 9.1 编排器调度的对象

编排器可以调度两类对象：

**A. 全局 Workflow Node**

例如：
1. Parse Task；
2. Load Playbook；
3. Build Context；
4. Generate Evidence Packets；
5. Dispatch Analysis Domain Jobs；
6. Detect Conflicts；
7. Run Evaluator；
8. Evaluate Playbook；
9. Generate Decision Candidate；
10. Run Guardrail Check；
11. Build Decision Trace。

**B. Analysis Domain Job**

例如：
1. Macro / Meso Job；
2. Fundamentals Job；
3. Company Event / Catalyst Job；
4. Sentiment Job；
5. Technical / Market Job。

编排器不调度能力域内部的具体模型、工具或 Agent。

### 9.2 编排器不应做什么

编排器不应：
1. 直接计算财务指标；
2. 直接解释技术指标；
3. 直接分析新闻情绪；
4. 直接进入能力域内部选择工具；
5. 绕过能力域输出格式；
6. 隐藏能力域之间的冲突；
7. 在数据不足时强行生成明确建议；
8. 绕过 Guardrails；
9. 替用户做最终投资决策。

### 9.3 编排模式

MVP 阶段主要支持三类编排模式。

#### 9.3.1 Fixed Workflow

适用于标准单股票分析。

特点：执行路径固定；结果稳定；易于审计；成本可控。

#### 9.3.2 Routing

适用于不同用户意图走不同流程。

例如：
- 是否买入 → single_stock_decision_workflow
- 财报怎么看 → earnings_review_workflow
- 为什么大跌 → event_explain_workflow
- 是否长期持有 → long_term_review_workflow

MVP 阶段可以先只实现 single_stock_decision_workflow。

#### 9.3.3 Parallel Domain Analysis

适用于五个能力域并行或准并行生成 Analysis Card。

MVP 阶段可以不强制物理并行，但逻辑上应保持能力域相互独立。

### 9.4 非 MVP 编排模式

以下编排模式可作为后续版本能力：
- Orchestrator-Workers；
- Evaluator-Optimizer 自动重写；
- Bull/Bear Debate；
- Multi-step Planning；
- Human-in-the-loop 审批；
- 多股票批量调度；
- 组合层工作流。

---

## 10. 标准单股票分析 Workflow

MVP 推荐优先实现标准单股票分析 Workflow。

### 10.1 Workflow 名称

`single_stock_standard_analysis_workflow`

### 10.2 适用场景

适用于用户想要对单只股票形成结构化投资判断的场景。

示例问题：
- 帮我分析一下这只股票现在是否值得关注。
- 按成长股中期持有逻辑看 NVDA。
- 这只股票下跌后是否值得买入？
- 我已经持有这只股票，现在应该继续持有吗？

### 10.3 Workflow 步骤

```
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
7. Validate Analysis Cards
  ↓
8. Detect Cross-domain Conflicts
  ↓
9. Evaluate Playbook Conditions
  ↓
10. Run Guardrail Check
  ↓
11. Generate Decision Candidate
  ↓
12. Build Decision Trace
  ↓
END
```

### 10.4 Step 1：Parse Investment Task

**输入**：用户自然语言请求

**输出**：Investment Task

任务解析应识别：标的；市场；用户意图；时间周期；投资风格；分析深度；是否涉及用户持仓；是否需要用户私有数据。

如果关键信息缺失，系统可以使用默认值，但必须在 Decision Trace 中标记默认假设。

### 10.5 Step 2：Load Investment Playbook

**输入**：Investment Task

**输出**：Playbook Context

如果用户未指定 Playbook，MVP 可使用默认 Playbook。

MVP 推荐默认 Playbook：**capital_cycle_fundamental_playbook**

该 Playbook 面向：资本周期投资者；产业周期投资者；中长期基本面投资者；关注宏观/中观与公司基本面关系的主动投资者。

Playbook 的完整定义由 SPEC-006 负责。

### 10.6 Step 3：Build Context Bundle

**输入**：Investment Task + Playbook Context

**输出**：Context Bundle

MVP 阶段 Context Bundle 至少包含：
1. 标的基本信息；
2. 最近价格数据；
3. 关键财务数据；
4. 公司公告或财报摘要；
5. 近期公司事件；
6. 情绪或新闻标题摘要；
7. 宏观/中观背景摘要；
8. 技术指标原始数据。

如果某类数据缺失，必须标记。

### 10.7 Step 4：Generate Evidence Packets

**输入**：Context Bundle

**输出**：Evidence Packet List

MVP 阶段可生成以下证据类型：
1. 财务质量证据；
2. 估值证据；
3. 公司事件证据；
4. 情绪证据；
5. 技术面证据；
6. 宏观/中观证据；
7. 数据质量证据。

**v0.2 要求**：每个 Evidence Packet 必须标记 `generation_mechanism`（computed / structured / interpreted）和 `freshness_level`（详见第 7、8 节）。

### 10.8 Step 5：Dispatch Analysis Domain Jobs

**输入**：Investment Task + Context Bundle + Evidence Packets + Playbook Constraints

**输出**：Analysis Domain Jobs

MVP 阶段默认调度五个能力域：
1. Macro / Meso；
2. Fundamentals；
3. Company Event / Catalyst；
4. Sentiment；
5. Technical / Market。

如果某个能力域缺少必要数据，则仍应返回 Analysis Card，但状态为：`insufficient_data`。

### 10.9 Step 6：Collect Analysis Cards

**输入**：Analysis Domain Jobs

**输出**：Analysis Card List

每个能力域必须返回一张 Analysis Card。

MVP 阶段不要求能力域物理并行，但要求输出结构一致。

### 10.10 Step 7：Validate Analysis Cards

**输入**：Analysis Card List

**输出**：Validation Report

MVP 阶段 Evaluator 只做检查和标注，不触发自动重写。

检查内容包括：
1. 是否缺少支持证据；
2. 是否缺少反方证据；
3. 是否缺少时间周期；
4. 是否缺少置信度；
5. 是否存在无证据判断；
6. 是否存在数据质量问题；
7. 是否存在过度自信表述。

**v0.2 要求**：Validation Report 按 Block / Flag / Note 三级输出，Orchestrator 必须根据 severity 采取不同处理路径（详见第 5.9 节和第 12.1 节）。

### 10.11 Step 8：Detect Cross-domain Conflicts

**输入**：Analysis Card List

**输出**：Conflict Report

常见冲突包括：
1. 基本面正面，但技术面破位；
2. 技术面正面，但情绪过热；
3. 事件催化正面，但估值过高；
4. 宏观环境压制估值，但公司增长强劲；
5. 情绪悲观，但基本面没有恶化；
6. 公司事件重大，但市场尚未反应。

Conflict Report 应进入 Decision Trace，并影响 Decision Candidate 的建议边界。

**v0.2 要求**：冲突按 low / medium / high 分级，按升级规则影响 Decision Candidate（详见第 13 节）。

### 10.12 Step 9：Evaluate Playbook Conditions

**输入**：Investment Playbook + Analysis Cards + Conflict Reports

**输出**：Playbook Evaluation Report

MVP 阶段 Playbook Evaluation 可以采用半结构化方式：
1. 列出 Playbook 条件；
2. 标记通过 / 不通过 / 部分通过 / 数据不足；
3. 记录对应证据；
4. 说明关键阻塞项；
5. 输出对 Decision Candidate 的影响。

**v0.2 要求**：Hard Constraint 必须由规则引擎执行；Soft Constraint 可由 LLM 辅助解释。Playbook Evaluation Report 通过 `recommended_decision_bounds` 约束建议空间（详见第 5.10 节）。

### 10.13 Step 10：Run Guardrail Check

**输入**：Decision Context

**输出**：Guardrail Report

MVP 阶段 Guardrails 至少包括：
1. 不承诺收益；
2. 不输出无依据强买入；
3. 数据不足时必须标记；
4. 模型预测不得表述为确定事实；
5. 不自动下单；
6. 高风险结论必须降级；
7. 反方证据缺失时不得输出强结论。

### 10.14 Step 11：Generate Decision Candidate

**输入**：Analysis Cards + Conflict Report + Playbook Evaluation Report + Guardrail Report

**输出**：Decision Candidate

Decision Candidate 应包含：
1. 建议动作；
2. 核心理由；
3. 适用投资风格；
4. 支持证据；
5. 阻塞因素；
6. 关键风险；
7. 失效条件；
8. 下一步检查项；
9. 置信度；
10. 是否需要人工复核。

**v0.2 要求**：Decision Candidate 的建议必须在 Playbook Evaluation Report 的 `recommended_decision_bounds` 范围内。如果未达到最小可用 Analysis Card 阈值，不应生成完整 Decision Candidate（详见第 14 节）。

### 10.15 Step 12：Build Decision Trace

**输入**：Full Run State

**输出**：Decision Trace

Decision Trace 应提供三层视图：
- **Level 1：结论摘要** — 面向快速阅读。
- **Level 2：模块分析** — 面向投研审阅。
- **Level 3：执行链路** — 面向复盘和审计。

完整设计由 SPEC-008 定义。

---

## 11. Playbook 在工作流中的介入点

Investment Playbook 不只在最后一步使用。它应在三个阶段介入。

### 11.1 前置介入

在任务解析和工作流选择阶段，Playbook 影响：
1. 需要运行哪些能力域；
2. 哪些能力域更重要；
3. 分析时间周期；
4. 是否需要特定数据；
5. 是否需要特定风险检查。

### 11.2 中置介入

在能力域执行阶段，Playbook 影响：
1. 每个能力域必须检查哪些问题；
2. Analysis Card 必须输出哪些字段；
3. 哪些证据必须被引用；
4. 哪些反方证据必须出现。

### 11.3 后置介入

在最终建议生成阶段，Playbook 影响：
1. 条件通过 / 不通过；
2. 是否允许强建议；
3. 是否需要降级；
4. 是否进入观察列表；
5. 是否触发人工复核。

MVP 阶段 Playbook 的执行机制是半结构化规则 + LLM 解释组合。**Hard Constraint 必须由规则引擎执行，LLM 仅用于 Soft Constraint 的辅助解释。**

完整 Playbook 执行机制由 SPEC-006 定义。

---

## 12. Review & Governance 接入点

### 12.1 Evaluator **[v0.2 重写]**

MVP 阶段 Evaluator 是检查器，不是自动优化器。它不自动重写分析结果，但必须有处理闭环。

#### 12.1.1 接入点

1. Analysis Card 生成后；
2. Decision Candidate 生成前。

#### 12.1.2 Evaluator Finding 处理闭环

| Severity | 触发条件示例 | 处理方式 |
|----------|-------------|----------|
| **Block** | 必要证据缺失；Fundamentals Card 缺失；Analysis Card 数量低于最低阈值；Guardrail 高风险；强建议缺少支持证据；Playbook 硬性条件无法判断 | 不生成强 Decision Candidate；输出 need_more_data 或 analysis_incomplete；要求用户补充数据或降低分析强度；在 Decision Trace 中展示阻塞原因 |
| **Flag** | 反方证据不足；数据质量较低；模块冲突未充分解释；置信度偏高；某些非必要能力域缺失 | 继续生成 Decision Candidate；降低置信度；在 Decision Trace 中展示警告；建议用户复核相关模块 |
| **Note** | 格式轻微问题；非关键字段缺失；低影响数据提示 | 记录 Event Log；可选择性展示在 Trace Level 3；不影响 Decision Candidate |

### 12.2 Guardrail Checker

Guardrail Checker 接入点：Decision Candidate 生成前后均可。

前置 Guardrail 用于阻止明显不合规或不可靠路径。

后置 Guardrail 用于检查最终表达是否越界。

### 12.3 Human-in-the-loop

MVP 阶段不强制实现完整人工审批流，但应预留状态。

以下场景可标记为需要人工复核：
1. 数据源冲突；
2. 重大突发事件；
3. 结论强烈但证据薄弱；
4. 用户持仓风险较高；
5. 模型置信度低；
6. Playbook 条件无法判断；
7. Guardrail 触发高风险标记；
8. **v0.2 增加**：High severity 冲突触发。

状态字段：
```json
{
  "requires_human_review": true,
  "review_reason": "重大事件影响路径不明确"
}
```

---

## 13. Conflict Report 对 Decision Candidate 的影响机制 **[v0.2 新增]**

Conflict Report 不只是展示对象，也必须影响 Decision Candidate 的边界。

### 13.1 冲突严重度

Conflict severity 分为：`low` / `medium` / `high`。

### 13.2 升级规则

MVP 阶段采用以下规则：

#### Low Conflict

**条件**：冲突数量 ≤ 1；severity = low；不涉及硬性 Playbook 条件；不涉及 Guardrail。

**处理**：正常生成 Decision Candidate；冲突进入 Decision Trace；置信度轻微下调。

#### Medium Conflict

**条件**：冲突数量为 1-2；或任一冲突 severity = medium；或涉及估值、情绪、技术等非硬性阻塞项。

**处理**：生成谨慎型 Decision Candidate；**禁止 strong buy / strong sell 表达**；建议动作优先使用 wait、add_to_watchlist、hold_if_already_owned；置信度中度下调。

#### High Conflict

**条件**：冲突数量 ≥ 2 且至少一个 severity = high；或 Fundamentals 与重大 Event 结论严重冲突；或 Playbook 硬性条件与能力域结论冲突；或证据质量不足但结论方向强烈。

**处理**：标记 `requires_human_review`；不生成强建议；输出 need_more_data、wait 或 analysis_incomplete；在 Decision Trace 中突出显示冲突。

---

## 14. 最小可用 Analysis Card 阈值 **[v0.2 新增]**

MVP 阶段不应在信息不足时强行生成 Decision Candidate。

### 14.1 默认阈值

生成 Decision Candidate 至少需要满足：
1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals Card **必须**可用；
3. 至少一个非 Fundamentals 的能力域提供有效支持或反方证据；
4. 至少没有 Block 级 Validation Finding；
5. Playbook 的关键硬性条件可以被判断。

### 14.2 未达到阈值时

如果未达到阈值，系统应输出 `analysis_incomplete` 或 `need_more_data`，而不是生成投资建议。

### 14.3 可例外场景

如果用户明确要求某一类专项分析（例如：只看技术面；只看财报；只解释事件；只做宏观背景分析），则不要求满足 3/5 阈值，但输出类型必须是专项分析，不是完整 Decision Candidate。

---

## 15. Macro / Meso MVP 实现层级 **[v0.2 重写]**

Macro / Meso 在 MVP 中保留为一级能力域，但不做完整宏观研究系统。

### 15.1 MVP 范围

MVP 阶段 Macro / Meso 只提供三个层级的信息：
1. Market Regime Context；
2. Industry / Capex Cycle Context；
3. Rate / Liquidity / Policy Context。

### 15.2 实现原则

MVP 阶段优先使用：
- 外部数据源已有指标；
- 人工维护或半结构化标签；
- 简单规则模型；
- 明确来源的政策或行业信息；
- 少量 Agentic 解释。

MVP 阶段不做：
- 自主宏观预测；
- 复杂 regime 推断；
- 完整行业供需模型；
- 宏观资产配置模型；
- 隐含宏观因子回归。

### 15.3 Macro / Meso Evidence 分类

Macro / Meso Evidence 必须标记来源类型（computed / structured / interpreted）。

**如果是 interpreted evidence，不得作为 Playbook 硬性条件的唯一依据。**

---

## 16. Sentiment MVP 降权策略 **[v0.2 新增]**

Sentiment 在 MVP 中保留为一级能力域，但默认视为高噪声能力域。

### 16.1 数据质量处理

如果 Sentiment Sources 数据质量为 low，则 Sentiment Card 仍可生成，但必须：
1. 标记低数据质量；
2. 降低默认置信度；
3. 不作为强建议的主要依据；
4. 不允许单独触发 buy / sell；
5. 主要用于风险提示、过热提示和叙事观察。

### 16.2 Sentiment 的默认角色

MVP 阶段 Sentiment 更适合回答：
- 市场是否过热；
- 是否存在恐慌；
- 是否存在叙事拥挤；
- 是否与基本面或事件出现背离；
- 是否需要用户谨慎追高或谨慎抄底。

Sentiment 不应在 MVP 中承担核心定价判断。

---

## 17. Event Log **[v0.2 重写]**

系统底层维护统一 Event Log。

### 17.1 MVP 最小 Schema

```json
{
  "event_id": "evt_001",
  "run_id": "run_001",
  "task_id": "task_001",
  "timestamp": "2026-06-14T10:30:00Z",
  "event_type": "node_completed",
  "node_id": "generate_evidence_packets",
  "node_type": "workflow_node",
  "input_refs": ["ctx_001"],
  "output_refs": ["ev_financial_001", "ev_technical_001"],
  "status": "success",
  "duration_ms": 1240,
  "error": null,
  "warnings": []
}
```

### 17.2 event_type 示例

MVP 阶段支持：`run_started` / `run_completed` / `node_started` / `node_completed` / `node_failed` / `model_called` / `tool_called` / `evidence_created` / `analysis_card_created` / `validation_finding_created` / `conflict_created` / `guardrail_triggered` / `decision_candidate_created` / `user_feedback_recorded`。

---

## 18. Observability 与 Decision Trace 的数据关系

Event Log 向上生成两个视图。

### 18.1 Observability View

面向开发和运维。

关注：
1. 系统是否稳定；
2. 哪个节点失败；
3. 哪个模型成本高；
4. 哪个工具延迟高；
5. 哪类任务失败率高。

### 18.2 Decision Trace View

面向投资用户。

关注：
1. 使用了哪些证据；
2. 哪些分析模块支持或反对；
3. 哪些冲突存在；
4. 哪些 Playbook 条件触发；
5. 为什么得到当前建议。

两者共享底层 Event Log，但不共享展示逻辑。

**三者关系**：
```
Event Log → Decision Trace
Event Log → Observability
```
Decision Trace 不应直接暴露全部 Event Log，而应筛选与投资判断相关的信息。

---

## 19. MVP 架构边界

### 19.1 MVP 应实现

MVP 应实现：
1. 单股票标准分析 Workflow；
2. Investment Task 解析；
3. 默认 Investment Playbook；
4. Context Bundle 构建；
5. Evidence Packet 生成（标记 generation_mechanism）；
6. 五个分析能力域返回 Analysis Card；
7. Conflict Detection（含 severity 分级）；
8. Evaluator 标注（Block / Flag / Note 三级）；
9. Guardrail Check；
10. Decision Candidate；
11. Decision Trace Level 1 和 Level 2；
12. 基础 Event Log（MVP 最小字段）。

### 19.2 MVP 暂不实现

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
10. Playbook Applicability Evaluator。

### 19.3 MVP 默认用户定位

MVP 优先面向：
1. 资本周期投资者；
2. 产业周期投资者；
3. 中长期基本面投资者；
4. 价值与成长结合型投资者；
5. 关注宏观/中观与公司基本面关系的主动投资者。

因此，Macro / Meso 在 MVP 中保留为一级能力域。

但 MVP 中 Macro / Meso 不做完整宏观研究系统，而聚焦：
1. Market Regime；
2. Industry Cycle；
3. Policy Context；
4. Capex Cycle；
5. Rate / Liquidity Context；
6. 对目标公司或行业估值环境的影响。

---

## 20. 错误与降级策略

### 20.1 数据缺失

如果某类数据缺失，系统不应中断整个工作流。

对应能力域应返回：`insufficient_data`

并说明：缺失数据；影响范围；是否影响最终建议；用户下一步应补充什么。

### 20.2 能力域失败

如果某个能力域执行失败，编排器应：
1. 记录错误；
2. 标记该能力域不可用；
3. 继续执行其他能力域；
4. 在 Decision Trace 中展示缺失影响；
5. 降低最终结论置信度。

### 20.3 证据冲突

如果证据冲突，系统不应自动消除。应生成 Conflict Report，并在最终建议中说明冲突如何影响判断。

**v0.2 增加**：冲突按升级规则影响 Decision Candidate 的建议边界（详见第 13 节）。

### 20.4 Guardrail 触发

如果 Guardrail 触发严重风险，系统应：
1. 降级最终建议；
2. 要求更多数据；
3. 提醒用户人工复核；
4. 避免强建议表达。

---

## 21. 状态模型

每次工作流运行应维护 Run State。

```json
{
  "run_id": "run_001",
  "task": "InvestmentTask",
  "playbook": "PlaybookContext",
  "context_bundle": "ContextBundle",
  "evidence_packets": [],
  "analysis_cards": [],
  "conflict_reports": [],
  "validation_report": null,
  "playbook_evaluation": null,
  "guardrail_report": null,
  "decision_candidate": null,
  "decision_trace": null,
  "event_log": [],
  "status": "running"
}
```

可能的状态：`pending` / `running` / `completed` / `completed_with_warnings` / `failed` / `requires_user_input` / `requires_human_review`。

---

## 22. Playbook Lifecycle **[v0.2 新增]**

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

---

## 23. Playbook 适用性风险 **[v0.2 新增]**

系统早期版本只判断资产是否符合指定 Playbook，不判断 Playbook 本身是否适合当前市场环境。

**这是已知局限性。**

未来需要 Playbook Applicability Evaluator，用于判断：
1. 当前市场 regime 是否适合该 Playbook；
2. Playbook 是否过严；
3. Playbook 是否过松；
4. 是否导致用户系统性错过机会；
5. 是否需要提示用户复审 Playbook。

该能力**不进入 MVP**。

---

## 24. 后续 SPEC 依赖

SPEC-003 与后续文档关系如下：

| SPEC | 负责定义 |
|------|---------|
| SPEC-004 | 五类分析能力域与 Analysis Card Schema |
| SPEC-006 | Investment Playbook 规范 |
| SPEC-007 | Orchestration 与执行路径 |
| SPEC-008 | Decision Trace 与 Observability |
| SPEC-009 | Governance、Guardrails、Evaluator 与人工介入 |

---

## 25. 开放问题

### 25.1 Playbook 执行机制

MVP 阶段 Playbook 可采用半结构化规则 + LLM 解释组合。

**v0.2 已明确**：Hard Constraint 必须由规则引擎执行，不得由 LLM 直接判断。长期需要进一步明确：
1. 哪些规则必须结构化；
2. 哪些判断允许 LLM 解释；
3. 哪些条件触发 Guardrail；
4. 如何测试 Playbook 是否被正确执行。

### 25.2 Playbook 适用性评估

当前架构只判断资产是否符合指定 Playbook。

未来需要判断：Playbook 是否适合当前市场 regime；Playbook 是否过严；Playbook 是否过松；Playbook 是否导致系统性错过机会。

该能力不进入 MVP。

### 25.3 多股票与组合层扩展

当前架构以单股票分析为中心。

未来需要扩展到：股票池初筛；多股票横向比较；组合风险暴露；仓位建议；组合层 Decision Trace。

### 25.4 用户私有数据接入

如果使用用户持仓、交易记录、历史分析或复盘笔记，需要独立数据治理机制。

相关内容由 SPEC-012 定义。

### 25.5 Playbook Constraints 参考数据源的不确定性 **[v0.2 新增]**

Hard Constraint 引用 Structured Evidence 作为输入时（例如 Market Regime 标签），如果该 Structured Evidence 本身置信度不足，规则引擎的"确定性"会被上游输入的不确定性污染。长期需要建立跨证据链的置信度传播模型。

---

## 26. SPEC-003 v0.2 总结

SPEC-003 v0.2 的核心修订是把"确定性优先"从设计理念升级为执行约束。

### 关键原则

1. Evidence Packet 必须标记生成机制（computed / structured / interpreted）。
2. Computed Evidence 优先于 Structured Evidence，Structured Evidence 优先于 Interpreted Evidence。
3. Playbook 的硬性条件必须由规则引擎或确定性逻辑执行。
4. LLM 可以解释 Playbook 条件，但不能替代硬性条件判断。
5. Evaluator 标注必须进入 Block / Flag / Note 处理路径。
6. Conflict Report 必须影响 Decision Candidate 的建议边界。
7. 未达到最小 Analysis Card 阈值时，不生成完整 Decision Candidate。
8. Macro/Meso 和 Sentiment 在 MVP 中必须明确能力边界和置信度限制。
9. Event Log 必须在 MVP 起步阶段就记录最小字段。
10. Playbook 必须支持版本记录，确保历史 Decision Trace 可复现。

### 核心架构承诺

```
Investment Task → Context Bundle → Evidence Packets
→ Analysis Domain Jobs → Analysis Cards → Conflict Report
→ Validation Report → Playbook Evaluation Report
→ Guardrail Check → Decision Candidate → Decision Trace
```

编排器调度全局 Workflow 节点和能力域级 Analysis Domain Job。能力域内部实现对编排器透明，只需返回标准 Analysis Card。

### v0.1 → v0.2 进化

> **v0.1**: Workflow first, Agent when needed.  
> **v0.2**: Deterministic first, Agentic when necessary, Traceable always.

---

*文档结束 | 版本 v0.2 | 项目 crosslens*
