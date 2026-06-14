# SPEC-003：Agentic 投研工作流架构 v0.3.3 微补丁

**版本：** v0.3.3  
**状态：** Draft  
**项目名称：** crosslens  
**依赖文档：** SPEC-001 v0.4  
**基线文档：** SPEC-003 Agentic投研工作流架构 v0.3.2.md  
**文档类型：** 架构规格微补丁  
**目标阶段：** 产品机制设计 / MVP 架构定义  

---

## 0. 版本说明

本文件是 SPEC-003 v0.3.2 的规范性微补丁。

在生成完整合并版之前，以下两份文件共同构成 SPEC-003 v0.3.3 的有效版本：

```text
SPEC-003 Agentic投研工作流架构 v0.3.2.md
+ SPEC-003 Agentic投研工作流架构 v0.3.3.md
```

若本补丁与 v0.3.2 正文存在冲突，以本补丁为准。

---

## 1. 修订目标

SPEC-003 v0.3.2 已经完成跨文档架构对齐、Hard Constraint 与证据确定性边界、能力域隔离、`domain_status`、用户私有数据类型和 URI 占位说明。

v0.3.3 不改变架构，只补齐三个规格完整性缺口：

1. Conflict escalation rules；
2. Event Log MVP schema；
3. Resolved Decision Bounds 正式 schema。

这三个对象直接影响 Decision Candidate 与 Decision Trace 的可实现性，因此需要在 SPEC-003 中给出最小可执行定义，而不是只留给后续 SPEC。

---

## 2. Conflict Escalation Rules

Conflict Report 不只是展示冲突，还必须影响 Resolved Decision Bounds 和 Decision Candidate。

### 2.1 Conflict severity

Conflict severity 可选值：

```text
low
medium
high
```

### 2.2 Conflict Report 最小 schema

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

### 2.3 severity 初始赋值规则

Conflict severity 不应完全由 LLM 判断。

MVP 阶段采用规则优先、LLM 辅助解释的方式。

#### Low conflict

满足以下任一条件时，可标记为 `low`：

1. 不涉及 Fundamentals；
2. 不涉及 Playbook Hard Constraint；
3. 冲突双方 confidence 均较低；
4. 主要基于 low quality Sentiment evidence；
5. 时间周期不一致但不影响当前任务。

默认影响：

```text
进入 Decision Trace，但不改变 allowed_actions。
```

可选影响：

```text
轻微降低 confidence_cap。
```

#### Medium conflict

满足以下任一条件时，可标记为 `medium`：

1. Fundamentals 与 Technical / Sentiment 出现方向冲突；
2. Company Event 与 Sentiment 出现方向冲突；
3. Macro / Meso 与估值或行业周期判断存在冲突；
4. Playbook Soft Constraint 与某个能力域结论冲突；
5. 冲突可能影响 suggested_action，但不足以阻断分析。

默认影响：

```text
移除强建议动作，保留谨慎动作。
```

例如：

```text
allowed_actions: wait, add_to_watchlist, hold_if_already_owned
```

#### High conflict

满足以下任一条件时，应标记为 `high`：

1. Fundamentals 与重大 Company Event 严重冲突；
2. Playbook Hard Constraint 与 Analysis Card 主结论冲突；
3. Guardrail 相关风险与 Decision Candidate 倾向冲突；
4. 高置信度 Computed Evidence 与高置信度能力域结论冲突；
5. 冲突足以阻止新开仓、加仓或强方向建议；
6. 多个 Medium conflict 指向同一风险方向。

默认影响：

```text
requires_human_review = true
```

并且：

```text
移除 buy / add_position / strong_buy / strong_sell 等强方向动作。
```

若冲突涉及关键 Hard Constraint，系统应输出：

```text
analysis_incomplete
```

或：

```text
requires_human_review
```

### 2.4 多冲突聚合规则

当存在多个 Conflict Report 时，系统按最严重冲突处理。

规则：

1. 任一 High conflict → 整体 conflict impact 至少为 high；
2. 两个及以上 Medium conflict 且指向同一风险方向 → 升级为 High；
3. Medium + 多个 Low conflict → 保持 Medium，但降低 confidence_cap；
4. 仅 Low conflict → 不改变 allowed_actions，仅进入 Decision Trace；
5. Conflict Report 的影响必须进入 Resolved Decision Bounds。

### 2.5 与 Validation / Guardrail 的关系

Conflict Escalation 不覆盖 Validation Block 或 Guardrail Block。

约束优先级仍为：

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

Conflict Escalation 主要用于：

1. 降低 confidence_cap；
2. 移除部分 allowed_actions；
3. 标记 requires_human_review；
4. 在 Decision Trace 中暴露冲突原因。

---

## 3. Event Log MVP Schema

Event Log 是 Observability 和 Decision Trace 的底层共享事件记录。

Decision Trace 可以选择性展示 Event Log 中与投资判断有关的事件；Observability 可以展示更完整的系统运行事件。

### 3.1 Event Log 最小 schema

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

### 3.2 必填字段

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

### 3.3 event_type 枚举

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

### 3.4 node_type 枚举

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

### 3.5 status 枚举

```text
success
failed
skipped
partial
blocked
warning
```

### 3.6 Decision Trace 对 Event Log 的依赖

Decision Trace 不需要展示完整 Event Log，但必须能从 Event Log 追溯以下问题：

1. 用户输入了什么任务；
2. 系统执行了哪些 Workflow 节点；
3. 生成了哪些 Evidence Packets；
4. 调度了哪些 Analysis Domain Jobs；
5. 生成了哪些 Analysis Cards；
6. 哪些 Validation / Conflict / Playbook / Guardrail 节点改变了建议边界；
7. Decision Candidate 是基于哪些上游对象生成的；
8. 是否发生错误、跳过、降级或人工复核标记。

### 3.7 MVP 必须记录的事件

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

## 4. Resolved Decision Bounds Schema

Resolved Decision Bounds 是 Decision Candidate 生成前的最终动作边界对象。

它负责合并来自以下对象的约束：

1. Validation Reports；
2. Conflict Reports；
3. Playbook Evaluation Report；
4. Guardrail Report；
5. User / Playbook preference，若适用。

Decision Candidate 只能从 Resolved Decision Bounds 的 `allowed_actions` 中选择 `suggested_action`。

### 4.1 Resolved Decision Bounds 最小 schema

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

### 4.2 allowed_actions 枚举

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

### 4.3 blocked_actions

`blocked_actions` 表示由于 Validation、Conflict、Playbook Evaluation 或 Guardrail 约束而不允许生成的动作。

例如：

1. Playbook 安全边际不足 → block `buy`；
2. Guardrail 触发数据不足 → block `buy` / `add_position`；
3. High conflict → block 强方向动作；
4. Sentiment 数据质量低 → block 高置信度买入表达。

### 4.4 requires_human_review

当任一上游对象要求人工复核时，Resolved Decision Bounds 必须标记：

```json
{
  "requires_human_review": true
}
```

典型触发：

1. High conflict；
2. Guardrail Block；
3. Validation Block；
4. Playbook Evaluation Report 返回 `requires_human_review`；
5. 关键数据缺失但用户仍要求结论。

### 4.5 confidence_cap

`confidence_cap` 是 Decision Candidate 的最高置信度上限。

规则：

1. Decision Candidate 的 `confidence` 不得高于 `confidence_cap`；
2. 每一次降低 confidence_cap 必须记录在 `confidence_cap_reason`；
3. `confidence_cap` 不得由 LLM 随机生成；
4. MVP 可采用规则表赋值；
5. 完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

### 4.6 allowed_actions 为空时的处理

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

### 4.7 与 Decision Candidate 的关系

Decision Candidate 必须引用 Resolved Decision Bounds：

```json
{
  "decision_candidate_id": "dc_001",
  "resolved_decision_bounds_id": "rdb_001",
  "suggested_action": "wait",
  "confidence": 0.58,
  "action_selection_reason": "allowed_actions 中包含 wait 和 add_to_watchlist；由于估值安全边际不足且存在中等冲突，选择 wait。"
}
```

Decision Candidate 的 `suggested_action` 必须满足：

```text
suggested_action ∈ allowed_actions
```

若不满足，Guardrail Checker 或 Evaluator 必须阻止输出。

---

## 5. v0.3.3 总结

SPEC-003 v0.3.3 不改变架构方向，只补齐三项规格完整性：

1. Conflict escalation rules；
2. Event Log MVP schema；
3. Resolved Decision Bounds 正式 schema。

本补丁使以下链条更加完整：

```text
Analysis Cards
  ↓
Validation Reports
  ↓
Conflict Reports
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

v0.3.3 继续坚持 crosslens 的架构宪法：

```text
Deterministic first, Agentic when necessary, Traceable always.
```
