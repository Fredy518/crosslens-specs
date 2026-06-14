# SPEC-009：Governance、Guardrails、Evaluator 与人工介入

**版本：** v0.1
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-004 v0.2.5；SPEC-006 v0.3.0；SPEC-007 v0.6
**文档类型：** 治理规范
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

v0.1 为 SPEC-009 初稿。

本版本承接 SPEC-003 §16（Guardrail Report）、SPEC-003 §17（Resolved Decision Bounds）、SPEC-006 §45 Q4（confidence_adjustment 自动修改机制）、SPEC-004 §26.1 NOTE（lineage 递归污染检测）中的 deferred 项，定义 Governance 层三组件的完整执行语义。

核心原则：

```text
Guardrails narrow bounds, not control flow.
Evaluator checks and flags, never auto-rewrites.
Human review must be aggregated into bounds.
Contamination must be detectable, not silently absorbed.
```

中文表达：

```text
Guardrail 收窄边界，不另开控制流。
Evaluator 检查标记，不自动重写。
人工复核信号必须汇聚到边界。
证据污染必须可检测，不能静默吸收。
```

---

## 1. 文档目标

SPEC-009 用于定义 crosslens 中 Governance 层的完整语义，包括：

1. Guardrail 系统的执行规则、action 语义和边界收窄算法；
2. Evaluator 的职责边界、质量评估规则和 confidence_cap 修改机制；
3. Human-in-the-loop 的触发条件汇聚、接口契约和降级策略；
4. 证据污染检测——lineage 递归检查的完整算法；
5. Governance 层与 Orchestration（SPEC-007）、Playbook（SPEC-006）、能力域（SPEC-004）的接口契约。

本 SPEC 不定义：
- Playbook 本身的约束逻辑（见 SPEC-006）；
- Orchestration 调度顺序（见 SPEC-007）；
- 各能力域的内部实现（见 SPEC-004）。

---

## 2. 架构总览：Governance 三组件

### 2.1 在 Workflow 中的位置

```text
                               Orchestration Layer
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
    ┌────▼─────┐              ┌───────▼───────┐           ┌───────▼───────┐
    │ GUARDRAIL │              │   EVALUATOR   │           │ HUMAN REVIEW  │
    │  SYSTEM   │              │               │           │   MANAGER     │
    │           │              │               │           │               │
    │ 拦截 &    │              │ 质量评估 &     │           │ 汇聚 &        │
    │ 边界收窄  │              │ 置信度修改     │           │ 路由          │
    └────┬─────┘              └───────┬───────┘           └───────┬───────┘
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      │
                              Resolved Decision Bounds
```

### 2.2 三组件协作时序

```text
Playbook Evaluation Report
         │
         ▼
   ┌─────────────────┐
   │ GUARDRAIL CHECK  │  ← 紧接 Playbook Evaluation 之后
   │ (收窄 bounds)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │   EVALUATOR      │  ← Guardrail 之后
   │ (质量评估+cap)   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────┐
   │ HUMAN REVIEW AGG     │  ← 汇聚所有上游 requires_human_review 信号
   │ (判定是否阻止输出)   │
   └────────┬────────────┘
            │
            ▼
   Resolved Decision Bounds
```

### 2.3 治理组件职责矩阵

| 组件 | 输入 | 输出 | 可否修改 bounds | 可否阻止 Candidate |
|---|---|---|---|---|
| Guardrail | Playbook Evaluation Report, Analysis Cards, Evidence Packets | Guardrail Report | ✅ 仅收窄 | ✅ block_new_position / require_human_review |
| Evaluator | 所有上游 Report + Cards | Evaluation Report | ✅ confidence_cap 修改 | ❌ 不直接阻止 |
| Human Review Agg | Guardrail Report, Evaluation Report, Conflict Report, Playbook Evaluation Report | requires_human_review flag | ❌ | ✅ 阻止 Candidate 生成 |

---

## 3. Guardrail 系统

### 3.1 Guardrail 定位

Guardrail 是 Governance 层的第一道防线。它的职责不是重新评估投资判断，而是检查系统输出是否违反了**不可妥协的安全和合规边界**。

Guardrail 与 Playbook Hard Constraint 的区别：

| | Playbook Hard Constraint | Guardrail |
|---|---|---|
| 定义者 | 用户（通过 Playbook） | 系统（硬编码） |
| 检查对象 | 投资条件 | 输出安全性 |
| 可配置 | ✅ | ❌（MVP 不可绕过） |
| 优先级 | 高 | 最高 |

### 3.2 Guardrail 执行时机

Guardrail 在 Playbook Evaluation 完成之后立即执行。

```
Playbook Evaluation → recommended_decision_bounds (初始 bounds)
    ↓
Guardrail Check → 检查 recommended_decision_bounds + Analysis Cards
    ↓
Guardrail Report → narrowed_bounds (收窄后的 bounds)
```

### 3.3 Guardrail 规则分类

```text
GUARDRAIL_RULES = {
    // 输出安全类
    "no_return_promise": {
        "severity": "critical",
        "description": "不得承诺收益或预测价格",
        "check": "decision_candidate text contains guaranteed return language",
        "action": "block_output"
    },
    "no_ungrounded_strong_opinion": {
        "severity": "critical", 
        "description": "无充分证据时不得输出强买入/强卖出",
        "check": "suggested_action in {strong_buy, strong_sell} AND confidence < 0.7",
        "action": "downgrade_to_neutral"
    },
    "no_hidden_opposing_evidence": {
        "severity": "high",
        "description": "不得隐藏反方证据",
        "check": "opposing_evidence present but not mentioned in action_selection_reason",
        "action": "require_disclosure"
    },

    // 数据充分性类
    "insufficient_data_guard": {
        "severity": "high",
        "description": "关键数据缺失时不得输出方向性建议",
        "check": "domain_status == insufficient_data for required domain",
        "action": "cap_action_to_wait_or_watchlist"
    },
    "stale_data_guard": {
        "severity": "medium",
        "description": "过期数据支撑的结论必须标注",
        "check": "constraint backed by stale data",
        "action": "require_freshness_warning"
    },

    // 模型输出安全类
    "no_certainty_from_uncertain_input": {
        "severity": "high",
        "description": "不得将低确定性输入表述为确定性事实",
        "check": "confidence > 0.8 AND primary_supporting_evidence has data_quality < medium",
        "action": "cap_confidence"
    }
}
```

### 3.4 Guardrail Decision Tree（伪代码）

```python
def apply_guardrails(
    playbook_eval_report: PlaybookEvaluationReport,
    analysis_cards: list[AnalysisCard],
    evidence_packets: list[EvidencePacket],
    conflict_report: ConflictReport | None
) -> GuardrailReport:
    """
    Guardrail 执行流程。
    关键原则：Guardrail 只能收窄 bounds，不能恢复被 Playbook 移除的动作。
    """

    findings = []
    blocked_actions = set()
    requires_disclosure = False
    confidence_cap_adjustments = []

    # --- Phase 1: 输出安全检查 ---

    # Rule: no_return_promise
    if has_return_promise_language(playbook_eval_report):
        findings.append(Finding(
            guardrail_id="no_return_promise",
            severity="critical",
            action="block_output",
            description="检测到收益承诺语言"
        ))
        blocked_actions.add("block_output")
        # block_output 是最严重的——终止输出
        return GuardrailReport(
            triggered=True,
            findings=findings,
            overall_status="blocked",
            blocked_actions=list(blocked_actions),
            requires_human_review=True
        )

    # Rule: no_ungrounded_strong_opinion
    for action in playbook_eval_report.recommended_decision_bounds:
        if action in {"strong_buy", "strong_sell"}:
            supporting_confidence = get_supporting_evidence_confidence(
                analysis_cards, playbook_eval_report
            )
            if supporting_confidence < 0.7:
                findings.append(Finding(
                    guardrail_id="no_ungrounded_strong_opinion",
                    severity="critical",
                    action="downgrade_to_neutral",
                    description=f"强建议 {action} 缺乏充分证据支撑"
                ))
                blocked_actions.add(action)

    # Rule: no_hidden_opposing_evidence
    if has_hidden_opposing_evidence(analysis_cards, playbook_eval_report):
        findings.append(Finding(
            guardrail_id="no_hidden_opposing_evidence",
            severity="high",
            action="require_disclosure",
            description="存在未被引用的反方证据"
        ))
        requires_disclosure = True

    # --- Phase 2: 数据充分性检查 ---

    # Rule: insufficient_data_guard
    if has_required_domain_insufficient(analysis_cards, playbook_eval_report):
        findings.append(Finding(
            guardrail_id="insufficient_data_guard",
            severity="high",
            action="cap_action_to_wait_or_watchlist",
            description="关键能力域数据不足"
        ))
        # 收窄允许的动作
        blocked_actions.update({"buy", "add_position", "strong_buy", "strong_sell"})

    # Rule: stale_data_guard
    stale_exports = find_stale_constraint_exports(analysis_cards)
    if stale_exports:
        findings.append(Finding(
            guardrail_id="stale_data_guard",
            severity="medium",
            action="require_freshness_warning",
            description=f"{len(stale_exports)} 个约束使用了过期数据"
        ))
        requires_disclosure = True

    # --- Phase 3: 模型输出安全检查 ---

    # Rule: no_certainty_from_uncertain_input
    primary_evidence_quality = get_primary_evidence_quality(
        playbook_eval_report, analysis_cards, evidence_packets
    )
    if primary_evidence_quality < QualityLevel.MEDIUM:
        findings.append(Finding(
            guardrail_id="no_certainty_from_uncertain_input",
            severity="high",
            action="cap_confidence",
            description="主要支撑证据质量不足，降低置信度上限"
        ))
        confidence_cap_adjustments.append(ConfidenceCapAdjustment(
            source="guardrail:no_certainty_from_uncertain_input",
            reason="主要支撑证据质量 < medium",
            cap_value=0.65
        ))

    # --- Phase 4: 确定 overall_status ---

    has_block = any(f.action == "block_output" for f in findings)
    has_critical = any(f.severity == "critical" for f in findings)
    has_high = any(f.severity == "high" for f in findings)

    if has_block:
        overall_status = "blocked"
    elif has_critical:
        overall_status = "requires_modification"
    elif has_high:
        overall_status = "passed_with_constraints"
    else:
        overall_status = "passed"

    return GuardrailReport(
        triggered=len(findings) > 0,
        findings=findings,
        overall_status=overall_status,
        blocked_actions=list(blocked_actions),
        requires_disclosure=requires_disclosure,
        confidence_cap_adjustments=confidence_cap_adjustments,
        requires_human_review=(has_critical or has_block)
    )
```

### 3.5 Guardrail 边界收窄算法

Guardrail 对 `recommended_decision_bounds` 的修改必须遵循以下约束：

```python
def narrow_bounds(
    playbook_bounds: list[str],
    guardrail_report: GuardrailReport
) -> list[str]:
    """
    从 Playbook 推荐的 bounds 中移除 Guardrail 禁止的动作。
    
    关键不变量：
    1. 只能移除动作，不能添加动作
    2. 不能恢复被 Playbook 已移除的动作
    3. 收窄操作记录在 Guardrail Report 和 Decision Trace 中
    """
    narrowed = set(playbook_bounds)

    for blocked in guardrail_report.blocked_actions:
        if blocked in narrowed:
            narrowed.remove(blocked)

    # 确保移除了强建议动作（已被 blocked）
    narrowed.discard("strong_buy")
    narrowed.discard("strong_sell")

    # 如果所有方向性动作都被移除，保留 wait
    directional_actions = {"buy", "add_position", "reduce_position", "sell"}
    if not (narrowed & directional_actions):
        narrowed.add("wait")

    return sorted(list(narrowed))
```

### 3.6 Guardrail Report Schema

```json
{
  "guardrail_report_id": "gr_001",
  "task_id": "task_001",
  "run_id": "run_001",
  "triggered": true,
  "findings": [
    {
      "guardrail_id": "insufficient_data_guard",
      "severity": "high",
      "description": "关键能力域 Sentiment 数据不足",
      "action": "cap_action_to_wait_or_watchlist",
      "evidence_refs": ["card_sentiment_001"]
    }
  ],
  "overall_status": "passed_with_constraints",
  "blocked_actions": ["buy", "strong_buy"],
  "requires_disclosure": false,
  "confidence_cap_adjustments": [
    {
      "source": "guardrail:no_certainty_from_uncertain_input",
      "reason": "主要支撑证据质量 < medium",
      "cap_value": 0.65
    }
  ],
  "requires_human_review": false
}
```

### 3.7 Guardrail 不变量

```text
1. Guardrail 只能收窄 allowed_actions，不得恢复被 Playbook 移除的动作。
2. Guardrail 不得另开控制流（不能从 GUARDRAIL_CHECKING 跳转到其他 phase）。
3. Guardrail 的 block_output 是唯一可以终止整个 Run 的 Guardrail action。
4. Guardrail 的所有 findings 必须进入 Decision Trace。
5. Guardrail 规则在 MVP 中硬编码，不可被 Playbook 绕过。
6. Guardrail 不重新评估投资条件——它只检查输出安全性和合规性。
```

---

## 4. Evaluator 系统

### 4.1 Evaluator 定位

Evaluator 是 Governance 层的质量评估组件。它的职责是**检查和标记**，而不是**自动修正**。

Evaluator 不自动重写的核心理由：
1. 自动重写隐藏了系统缺陷——用户看不到问题，就无从改进；
2. 自动重写可能引入新错误——Evaluator 本身也是 LLM，有 hallucination 风险；
3. Token 成本——Evaluator-Optimizer 循环会导致成本失控。

### 4.2 Evaluator 执行时机

```
Guardrail Check → Guardrail Report
    ↓
Evaluator → 读取所有上游 Reports + Cards
    ↓
Evaluation Report (质量标记 + confidence_cap 修改)
```

### 4.3 Evaluator 检查维度

```text
EVALUATION_DIMENSIONS = {
    "evidence_quality": {
        "description": "支撑证据的充分性和质量",
        "checks": [
            "每个关键结论是否有至少一个 Computed Evidence 支撑",
            "Interpreted Evidence 占比是否过高 (>40%)",
            "是否存在过时的证据引用"
        ]
    },
    "reasoning_coherence": {
        "description": "推理链的自洽性",
        "checks": [
            "supporting_reasons 与 opposing_reasons 是否自相矛盾",
            "action_selection_reason 是否与 evidence 一致",
            "reasoning_chain 是否有断裂（缺失中间步骤）"
        ]
    },
    "confidence_calibration": {
        "description": "置信度标定的合理性",
        "checks": [
            "confidence 是否显著高于支撑证据质量",
            "confidence 是否低于最低阈值",
            "confidence_cap 是否需要下调"
        ]
    },
    "completeness": {
        "description": "分析覆盖的完整性",
        "checks": [
            "所有 required domains 是否产生 valid Analysis Card",
            "是否存在 missing_required_evidence",
            "opposing_evidence 是否被充分记录"
        ]
    }
}
```

### 4.4 Evaluator Decision Tree（伪代码）

```python
def run_evaluator(
    analysis_cards: list[AnalysisCard],
    playbook_eval_report: PlaybookEvaluationReport,
    guardrail_report: GuardrailReport,
    conflict_report: ConflictReport | None,
    validation_reports: list[ValidationReport]
) -> EvaluationReport:
    """
    Evaluator 执行流程。
    关键原则：检查 + 标记，不自动重写。
    """

    findings = []
    quality_flags = set()
    confidence_cap_adjustments = []

    # --- Phase 1: 证据质量评估 ---

    primary_evidence = extract_primary_evidence(analysis_cards, playbook_eval_report)
    computed_count = count_by_type(primary_evidence, "computed")
    interpreted_count = count_by_type(primary_evidence, "interpreted")
    total_primary = len(primary_evidence)

    if total_primary > 0:
        interpreted_ratio = interpreted_count / total_primary
        if interpreted_ratio > 0.4:
            findings.append(EvaluationFinding(
                dimension="evidence_quality",
                severity="warning",
                description=f"Interpreted Evidence 占比 {interpreted_ratio:.0%}，超过 40% 阈值",
                recommended_action="consider_regenerating_with_better_data"
            ))
            quality_flags.add("high_interpreted_ratio")
            confidence_cap_adjustments.append(ConfidenceCapAdjustment(
                source="evaluator:high_interpreted_ratio",
                reason=f"Interpreted Evidence 占比 {interpreted_ratio:.0%}",
                cap_value=0.60
            ))

    if computed_count == 0 and total_primary > 0:
        findings.append(EvaluationFinding(
            dimension="evidence_quality",
            severity="warning",
            description="无 Computed Evidence 支撑关键结论",
            recommended_action="review_evidence_sources"
        ))
        quality_flags.add("no_computed_evidence")
        confidence_cap_adjustments.append(ConfidenceCapAdjustment(
            source="evaluator:no_computed_evidence",
            reason="关键结论无 Computed Evidence 支撑",
            cap_value=0.55
        ))

    # --- Phase 2: 推理自洽性检查 ---

    contradictions = find_internal_contradictions(analysis_cards, playbook_eval_report)
    if contradictions:
        findings.append(EvaluationFinding(
            dimension="reasoning_coherence",
            severity="error",
            description=f"检测到 {len(contradictions)} 处推理矛盾",
            details=contradictions,
            recommended_action="review_and_correct"
        ))
        quality_flags.add("internal_contradiction")

    # --- Phase 3: 置信度标定 ---

    for card in analysis_cards:
        if card.confidence > 0.8 and card.data_quality == "low":
            findings.append(EvaluationFinding(
                dimension="confidence_calibration",
                severity="warning",
                description=f"{card.domain} 置信度 {card.confidence} 与 data_quality=low 不匹配",
                recommended_action="lower_confidence"
            ))
            quality_flags.add("miscalibrated_confidence")

    # --- Phase 4: 完整性检查 ---

    missing_required = find_missing_required_evidence(analysis_cards, playbook_eval_report)
    if missing_required:
        findings.append(EvaluationFinding(
            dimension="completeness",
            severity="warning",
            description=f"缺失 {len(missing_required)} 项必需证据",
            details=missing_required,
            recommended_action="request_missing_data"
        ))
        quality_flags.add("incomplete_coverage")

    # --- Phase 5: 确定 overall_quality ---

    has_error = any(f.severity == "error" for f in findings)
    has_warning = any(f.severity == "warning" for f in findings)

    if has_error:
        overall_quality = "needs_revision"
    elif has_warning:
        overall_quality = "acceptable_with_caveats"
    else:
        overall_quality = "acceptable"

    return EvaluationReport(
        evaluation_report_id=generate_id("eval"),
        task_id=analysis_cards[0].task_id,
        run_id=analysis_cards[0].run_id,
        findings=findings,
        quality_flags=list(quality_flags),
        overall_quality=overall_quality,
        confidence_cap_adjustments=confidence_cap_adjustments
    )
```

### 4.5 confidence_cap 修改规则

SPEC-009 承接 SPEC-006 §45 Q4 中 deferred 的 `confidence_adjustment` Preference 自动修改机制。

```python
def compute_final_confidence_cap(
    playbook_recommended_cap: float,       # 来自 Playbook Evaluation
    guardrail_adjustments: list[ConfidenceCapAdjustment],  # 来自 Guardrail
    evaluator_adjustments: list[ConfidenceCapAdjustment],  # 来自 Evaluator
    preference_adjustments: list[ConfidenceCapAdjustment], # 来自 Playbook Preference
) -> tuple[float, list[ConfidenceCapReason]]:
    """
    合并所有来源的 confidence_cap 调整。
    
    规则：
    1. 初始值 = playbook_recommended_cap (或默认 1.0)
    2. 按优先级从高到低叠加调整：Guardrail > Evaluator > Preference
    3. 同来源多个调整取最严格（最低 cap）
    4. 每层调整后 cap 不得低于上一层的值（只能继续收窄）
    5. 最终 cap < 0.5 时触发 requires_human_review
    
    叠加语义：取各层最严格值，不是简单相加。
    """
    
    reasons = []
    current_cap = playbook_recommended_cap if playbook_recommended_cap else 1.0

    # Layer 1: Guardrail adjustments (最高优先级)
    if guardrail_adjustments:
        # 取最严格的 Guardrail 调整
        strictest_gr = min(adj.cap_value for adj in guardrail_adjustments)
        if strictest_gr < current_cap:
            current_cap = strictest_gr
            reasons.append(ConfidenceCapReason(
                source_type="guardrail",
                source_ref=guardrail_adjustments[0].source,
                reason="Guardrail 触发置信度上限收窄",
                effect=f"cap_confidence_at_{current_cap}"
            ))

    # Layer 2: Evaluator adjustments
    if evaluator_adjustments:
        strictest_ev = min(adj.cap_value for adj in evaluator_adjustments)
        if strictest_ev < current_cap:
            current_cap = strictest_ev
            reasons.append(ConfidenceCapReason(
                source_type="evaluator",
                source_ref=evaluator_adjustments[0].source,
                reason="Evaluator 检测到质量问题，降低置信度上限",
                effect=f"cap_confidence_at_{current_cap}"
            ))

    # Layer 3: Preference adjustments (MVP: only confidence_adjustment type)
    if preference_adjustments:
        strictest_pref = min(adj.cap_value for adj in preference_adjustments)
        if strictest_pref < current_cap:
            current_cap = strictest_pref
            reasons.append(ConfidenceCapReason(
                source_type="preference",
                source_ref=preference_adjustments[0].source,
                reason="Playbook Preference 调整置信度上限",
                effect=f"cap_confidence_at_{current_cap}"
            ))

    return current_cap, reasons
```

**confidece_cap 边界值语义：**

| cap 范围 | 含义 |
|---|---|
| ≥ 0.70 | 高置信度区域——可支持强建议 |
| 0.55 - 0.69 | 中等置信度——支持谨慎方向性建议 |
| 0.50 - 0.54 | 低置信度——仅支持 wait/watchlist |
| < 0.50 | 不可接受——触发 requires_human_review |

### 4.6 Evaluator 不变量

```text
1. Evaluator 不得自动重写 Analysis Card、Playbook Evaluation Report 或 Decision Candidate。
2. Evaluator 的所有 findings 和建议必须进入 Decision Trace。
3. Evaluator 的 quality_flags 不得被下游组件忽略。
4. Evaluator 降级 confidence_cap 必须记录完整理由链。
5. Evaluator 不直接阻止 Candidate 生成（通过 confidence_cap < 0.5 间接触发 human_review）。
6. Evaluator 不应在 MVP 中触发自动重生成循环（Token 成本考虑）。
```

---

## 5. Human-in-the-loop

### 5.1 人工介入定位

Human-in-the-loop 不是 Governance 层的一个独立"步骤"，而是一个**信号汇聚和路由机制**。

`requires_human_review` 可以从多个上游来源产生，最终汇聚到 Resolved Decision Bounds。

### 5.2 触发条件汇聚

```python
def aggregate_human_review_signals(
    guardrail_report: GuardrailReport,
    evaluation_report: EvaluationReport,
    conflict_report: ConflictReport | None,
    playbook_eval_report: PlaybookEvaluationReport,
    resolved_cap: float,
    analysis_cards: list[AnalysisCard]
) -> tuple[bool, list[HumanReviewTrigger]]:
    """
    汇聚所有 requires_human_review 信号。
    
    来源（按处理顺序）：
    1. Guardrail Report
    2. Conflict Report (has_blocking_conflict)
    3. Playbook Evaluation Report (ambiguous_label_ref 等)
    4. Evaluator (confidence_cap < 0.5)
    5. Macro 域缺失 + 实际冲突
    6. Fundamentals 域不可用
    """

    triggers = []
    requires_review = False

    # Source 1: Guardrail
    if guardrail_report.requires_human_review:
        triggers.append(HumanReviewTrigger(
            source="guardrail",
            source_ref=guardrail_report.guardrail_report_id,
            trigger_type="guardrail_block_or_critical",
            description=f"Guardrail {guardrail_report.findings[0].guardrail_id} 触发人工复核"
        ))
        requires_review = True

    # Source 2: Conflict Report
    if conflict_report and conflict_report.has_blocking_conflict:
        triggers.append(HumanReviewTrigger(
            source="conflict_report",
            source_ref=conflict_report.conflict_report_id,
            trigger_type="blocking_conflict",
            description=f"Conflict '{conflict_report.conflicts[0].conflict_type}' 被标记为 blocking"
        ))
        requires_review = True

    # Source 3: Playbook - ambiguous_label_ref
    if playbook_eval_report.overall_result == "requires_human_review":
        triggers.append(HumanReviewTrigger(
            source="playbook_evaluation",
            source_ref=playbook_eval_report.playbook_evaluation_report_id,
            trigger_type="playbook_requires_review",
            description="Playbook Evaluation 无法自动判定"
        ))
        requires_review = True

    # Source 4: confidence_cap < 0.5
    if resolved_cap < 0.50:
        triggers.append(HumanReviewTrigger(
            source="evaluator",
            source_ref=evaluation_report.evaluation_report_id,
            trigger_type="confidence_cap_below_threshold",
            description=f"最终 confidence_cap = {resolved_cap} < 0.5"
        ))
        requires_review = True

    # Source 5: Macro 域缺失 + 实际冲突
    macro_card = find_card(analysis_cards, "macro_meso")
    if macro_card and macro_card.domain_status == "partial":
        if conflict_report and has_conflict_type(conflict_report, "macro_regime_vs_playbook"):
            triggers.append(HumanReviewTrigger(
                source="orchestration",
                source_ref=conflict_report.conflict_report_id,
                trigger_type="macro_partial_with_conflict",
                description="Macro/Meso 域数据不完整且存在 Playbook 冲突"
            ))
            requires_review = True

    # Source 6: Fundamentals 域不可用（从 SPEC-003 继承）
    fundamentals_card = find_card(analysis_cards, "fundamentals")
    if not fundamentals_card or fundamentals_card.domain_status in {"insufficient_data", "error"}:
        triggers.append(HumanReviewTrigger(
            source="orchestration",
            source_ref="task_config",
            trigger_type="fundamentals_unavailable",
            description="Fundamentals 能力域不可用——无法生成 Decision Candidate"
        ))
        requires_review = True

    return requires_review, triggers
```

### 5.3 人工复核后的路由

```python
def route_after_human_review(
    requires_review: bool,
    triggers: list[HumanReviewTrigger],
    run_config: RunConfig
) -> RouteDecision:
    """
    MVP 路由策略：
    - requires_human_review = true → 阻止 Candidate 生成
    - 输出 user_visible_status = 'requires_human_review'
    - 生成 Decision Trace（包含所有 triggers）
    """

    if requires_review:
        # MVP: 直接阻止，不生成 Candidate
        return RouteDecision(
            action="block_candidate",
            user_visible_status="requires_human_review",
            user_visible_reason=build_review_reason(triggers),
            next_step="present_to_user_for_review"
        )

    # 无人工复核需求 → 正常流程
    return RouteDecision(
        action="proceed_to_candidate",
        user_visible_status=None,
        next_step="generate_candidate"
    )
```

### 5.4 MVP 人工复核接口

```json
{
  "human_review_request": {
    "request_id": "hrr_001",
    "task_id": "task_001",
    "run_id": "run_001",
    "reason": "Guardrail 触发 + 估值安全边际不足",
    "triggers": [
      {
        "source": "guardrail",
        "trigger_type": "guardrail_block_or_critical",
        "description": "检测到关键 Guardrail 违规"
      }
    ],
    "available_data": {
      "analysis_cards_summary": "...",
      "conflict_summary": "...",
      "playbook_evaluation_summary": "..."
    },
    "suggested_user_actions": [
      "review_guardrail_findings",
      "adjust_playbook_constraints",
      "provide_additional_data",
      "override_and_proceed"
    ],
    "decision_trace_ref": "trace_001"
  }
}
```

### 5.5 Human-in-the-loop 不变量

```text
1. requires_human_review 不是 action——它不能出现在 allowed_actions 或 suggested_action 中。
2. requires_human_review 在 MVP 中阻止 Candidate 生成（不生成 Decision Candidate）。
3. 所有人工复核触发条件必须记录在 Decision Trace 中。
4. 人工复核触发后不得静默降级（必须显式通知用户）。
5. MVP 中不支持 human_review_mode = allow_labeled_candidate（见 SPEC-007 §57 MVP 暂不实现）。
6. requires_human_review 不短路剩余评估——系统应完成所有检查再汇聚信号。
```

---

## 6. 证据污染检测

### 6.1 污染检测定位

证据污染检测是对 SPEC-004 §26.1 NOTE 中 lineage 递归检查的实现。

问题场景：
```
Source Event → Interpreted Evidence (LLM 生成) → Structured Evidence → Hard Constraint
                                                    ↑
                                          这里已经有污染风险——
                                          Structured Evidence 的输入来自 LLM 输出
```

当前 SPEC-004 的 lineage 约束只检查 source event 的直接 Evidence Packet，无法检测间接污染。

### 6.2 污染检测算法

```python
def check_evidence_contamination(
    evidence: EvidencePacket,
    evidence_registry: dict[str, EvidencePacket],
    max_depth: int = 3
) -> ContaminationResult:
    """
    递归检查 Evidence Packet 的 lineage 是否存在污染。

    污染定义：
    - 任意祖先 Evidence 的 generation_type = "interpreted" → 污染
    - 任意祖先 Evidence 的 determinism_level = "low" → 潜在污染

    返回：
    - contamination_level: "clean" | "potentially_contaminated" | "contaminated"
    - contamination_path: 从当前 evidence 到污染源的路径
    """

    if max_depth <= 0:
        return ContaminationResult("unknown", [], "max_depth_exceeded")

    # Check self
    if evidence.generation_type == "interpreted":
        return ContaminationResult(
            "contaminated",
            [evidence.evidence_id],
            f"Evidence {evidence.evidence_id} 本身是 Interpreted"
        )

    if evidence.determinism_level == "low":
        return ContaminationResult(
            "potentially_contaminated",
            [evidence.evidence_id],
            f"Evidence {evidence.evidence_id} 确定性等级为 low"
        )

    # Check lineage
    if not hasattr(evidence, 'lineage') or not evidence.lineage:
        # 没有 lineage 信息 → 无法确定，标记为未知
        return ContaminationResult("unknown", [], "lineage_not_tracked")

    # 递归检查祖先
    for parent_ref in evidence.lineage.parent_evidence_refs:
        parent = evidence_registry.get(parent_ref)
        if parent is None:
            continue

        result = check_evidence_contamination(parent, evidence_registry, max_depth - 1)
        if result.contamination_level != "clean":
            # 将当前 evidence 加入污染路径
            full_path = result.contamination_path + [evidence.evidence_id]
            return ContaminationResult(
                result.contamination_level,
                full_path,
                f"通过 lineage 传播: {result.reason}"
            )

    return ContaminationResult("clean", [], "")
```

### 6.3 污染标记传播

```python
def propagate_contamination_to_hard_constraint(
    constraint_result: ConstraintEvaluationResult,
    input_evidence: list[EvidencePacket],
    evidence_registry: dict[str, EvidencePacket]
) -> ContaminationPropagation:
    """
    当 Hard Constraint 引用的 evidence 被检测到污染时，
    标记该 Constraint 为 contaminated。
    
    效果：
    1. 该 Hard Constraint 结果降级为 "contaminated"
    2. 在 Decision Trace 中标注污染的完整路径
    3. 在 Resolved Decision Bounds 中降低 confidence_cap
    4. 不自动将 Hard Constraint 降为 Soft Constraint
       （降级策略由 Playbook 或 Governance 层显式决策，不自动执行）
    """

    contaminations = []
    for evidence in input_evidence:
        result = check_evidence_contamination(evidence, evidence_registry)
        if result.contamination_level in {"contaminated", "potentially_contaminated"}:
            contaminations.append({
                "evidence_id": evidence.evidence_id,
                "contamination_level": result.contamination_level,
                "contamination_path": result.contamination_path,
                "reason": result.reason
            })

    if not contaminations:
        return ContaminationPropagation(
            constraint_id=constraint_result.constraint_id,
            is_contaminated=False
        )

    return ContaminationPropagation(
        constraint_id=constraint_result.constraint_id,
        is_contaminated=True,
        contaminations=contaminations,
        recommended_action="flag_for_human_review",
        confidence_cap_impact=0.10  # 降低 0.10
    )
```

### 6.4 污染检测责任边界

| 检测层级 | 负责 SPEC | 检测范围 |
|---|---|---|
| Evidence 层 lineage 记录 | SPEC-005 (Capability Package) | 工具调用链 lineage 记录 |
| 直接 lineage 检查 | SPEC-004 (§26.1) | source event 的直接 Evidence Packet |
| 递归污染检测 | SPEC-009 (§6) | 完整 lineage 树的递归遍历 |
| 污染响应策略 | SPEC-009 (§6) | 标记、降级、人工复核触发 |

---

## 7. Governance 层与各 SPEC 的接口契约

### 7.1 与 SPEC-003（架构）的接口

| 接口点 | SPEC-003 定义 | SPEC-009 承接 |
|---|---|---|
| Guardrail Report schema | §16 | §3.6 完整语义 |
| Resolved Decision Bounds | §17 | §8 合并算法 |
| confidence_cap 规则 | §17.4 | §4.5 修改规则 |
| Evaluator 位置 | §1.7 | §4 完整执行语义 |
| Human-in-the-loop 位置 | §17.2 | §5 汇聚和路由 |

### 7.2 与 SPEC-004（能力域）的接口

| 接口点 | SPEC-004 定义 | SPEC-009 承接 |
|---|---|---|
| lineage 递归检查 | §26.1 NOTE (deferred) | §6.2 完整算法 |
| `completed + unavailable` 禁止 | §5.3, §41 | §4.4 完整性检查 |
| `can_support_hard_constraint` | §9.1 | §3.3 insufficient_data_guard |
| `data_quality` 枚举 | §5.2 | §4.3 evidence_quality 评估 |

### 7.3 与 SPEC-006（Playbook）的接口

| 接口点 | SPEC-006 定义 | SPEC-009 承接 |
|---|---|---|
| `confidence_adjustment` 自动修改 | §45 Q4 (deferred) | §4.5 完整规则 |
| `block_*` 动作收窄 | §22-§24 | §3.5 边界收窄 |
| `requires_human_review` 触发 | §26-§27 | §5.2 汇聚 |
| Interpreted Evidence 降级 | §45 Q4 | §4.4 质量评估 |

### 7.4 与 SPEC-007（Orchestration）的接口

| 接口点 | SPEC-007 定义 | SPEC-009 承接 |
|---|---|---|
| GUARDRAIL_CHECKING state | §9 | §3.4 执行流程 |
| `requires_human_review` 汇聚 | §20-§22 | §5.2 完整汇聚 |
| Guardrail 只能收窄 bounds | §17 | §3.5 算法 |
| RunFlags 传播 | §18-§19 | §8.4 治理 flag |

---

## 8. Resolved Decision Bounds 完整合并算法

### 8.1 合并流程

```python
def resolve_decision_bounds(
    playbook_bounds: list[str],
    guardrail_report: GuardrailReport,
    evaluation_report: EvaluationReport,
    conflict_report: ConflictReport | None,
    analysis_cards: list[AnalysisCard],
    evidence_registry: dict[str, EvidencePacket]
) -> ResolvedDecisionBounds:
    """
    从所有上游来源合并生成最终 Resolved Decision Bounds。
    
    合并顺序（严格单向收窄）：
    1. 初始 bounds = playbook recommended_decision_bounds
    2. Guardrail 收窄 → narrowed_bounds
    3. 污染检测 → contamination_adjustments
    4. Evaluator → confidence_cap 调整
    5. Human Review 汇聚 → requires_human_review
    6. 冲突约束 → conflict_narrowing (仅从 Conflict Handling)
    """

    reasons = []
    applied_rules = []

    # Step 1: 初始 bounds
    allowed_actions = set(playbook_bounds)
    reasons.append(ReasonEntry(
        source="playbook_evaluation",
        action="initial_bounds",
        detail=f"Playbook recommended: {playbook_bounds}"
    ))

    # Step 2: Guardrail 收窄
    for blocked in guardrail_report.blocked_actions:
        if blocked in allowed_actions:
            allowed_actions.discard(blocked)
            reasons.append(ReasonEntry(
                source="guardrail",
                action="remove",
                detail=f"Guardrail removed '{blocked}'"
            ))
            applied_rules.append(f"guardrail:block_{blocked}")

    # Step 3: 污染检测
    contaminations = []
    for card in analysis_cards:
        for export_ in card.constraint_exports:
            if export_.can_support_hard_constraint:
                evidence = evidence_registry.get(export_.evidence_ref)
                if evidence:
                    result = check_evidence_contamination(evidence, evidence_registry)
                    if result.contamination_level != "clean":
                        contaminations.append(result)

    if contaminations:
        # 移除可能已被污染的强建议
        allowed_actions.discard("strong_buy")
        allowed_actions.discard("strong_sell")
        reasons.append(ReasonEntry(
            source="contamination_detection",
            action="remove",
            detail=f"检测到 {len(contaminations)} 处证据污染"
        ))

    # Step 4: Evaluator confidence_cap 调整
    confidence_cap, cap_reasons = compute_final_confidence_cap(
        playbook_recommended_cap=1.0,  # default
        guardrail_adjustments=guardrail_report.confidence_cap_adjustments,
        evaluator_adjustments=evaluation_report.confidence_cap_adjustments,
        preference_adjustments=[]
    )

    # Step 5: requires_human_review 汇聚
    requires_review, review_triggers = aggregate_human_review_signals(
        guardrail_report=guardrail_report,
        evaluation_report=evaluation_report,
        conflict_report=conflict_report,
        playbook_eval_report=None,  # 已合并到 bounds
        resolved_cap=confidence_cap,
        analysis_cards=analysis_cards
    )

    # Step 6: 最终 bounds 检查
    if not allowed_actions:
        allowed_actions = {"wait"}

    return ResolvedDecisionBounds(
        resolved_decision_bounds_id=generate_id("rdb"),
        task_id=analysis_cards[0].task_id,
        run_id=analysis_cards[0].run_id,
        allowed_actions=sorted(list(allowed_actions)),
        blocked_actions=[],  # 在 upstream 中跟踪
        requires_human_review=requires_review,
        human_review_triggers=review_triggers,
        confidence_cap=confidence_cap,
        confidence_cap_reason=cap_reasons,
        applied_rules=applied_rules,
        reasoning=reasons,
        contamination_findings=contaminations
    )
```

### 8.2 不允许的动作组合

```text
# 硬性禁止的组合
forbidden_combinations = {
    ("buy", "sell"),           # 不可同时买入卖出
    ("strong_buy", "sell"),    # 不可同时强买和卖出
    ("buy", "strong_sell"),    # 不可同时买入和强卖
    ("strong_buy", "strong_sell"),  # 不可同时强买强卖
}

# 如果 Resolved Bounds 包含禁止组合，降级为 wait + human_review
```

### 8.3 Governance Flag 传播

```python
# Governance flags 从各组件汇聚到 RunFlags

RUN_FLAG_GOVERNANCE_MAP = {
    "guardrail_triggered": "guardrail_report.triggered == True",
    "guardrail_blocked": "guardrail_report.overall_status == 'blocked'",
    "evaluator_warning": "evaluation_report.overall_quality != 'acceptable'",
    "evidence_contaminated": "len(contamination_findings) > 0",
    "confidence_capped": "confidence_cap < 1.0",
    "requires_human_review": "aggregated requires_human_review == True",
}
```

---

## 9. MVP 实现边界

### 9.1 必须实现

1. Guardrail 规则引擎——至少包含 6 条 Guardrail 规则（§3.3）；
2. Guardrail 边界收窄算法——只能移除动作（§3.5）；
3. Evaluator 四维质量检查——证据质量、推理自洽、置信度标定、完整性（§4.3）；
4. confidence_cap 合并算法——取各层最严格值（§4.5）；
5. Human Review 汇聚——六来源信号合并（§5.2）；
6. `requires_human_review` 阻止 Candidate 生成（§5.3）；
7. Guardrail Report、Evaluation Report 的完整 schema 输出；
8. Governance 层所有 findings 写入 Decision Trace；
9. 证据污染检测——递归 lineage 检查（§6.2）；
10. Resolved Decision Bounds 完整合并流程（§8.1）。

### 9.2 MVP 暂不实现

1. Evaluator 自动触发重生成循环（Token 成本考虑）；
2. `human_review_mode = allow_labeled_candidate`（见 SPEC-007 §57）；
3. Guardrail 规则的可视化配置界面；
4. 自适应 Guardrail 阈值（基于历史案例学习）；
5. 实时 Human Review 交互界面（仅支持异步 review 提示）；
6. 跨 Run 的治理质量趋势分析；
7. 证据污染的自动修复；
8. Governance 规则的 A/B 测试。

---

## 10. 核心不变量

```text
1. Guardrail 只能收窄 allowed_actions，不得恢复被 Playbook 移除的动作。
2. Guardrail 不得另开控制流。
3. Evaluator 检查 + 标记，不自动重写。
4. requires_human_review 不是 action——不能出现在 allowed_actions 或 suggested_action 中。
5. requires_human_review 在 MVP 中阻止 Candidate 生成。
6. 所有人工复核触发条件必须记录在 Decision Trace。
7. confidence_cap 不得由 LLM 随机生成。
8. confidence_cap 收窄方向单向：只能降低，不能提高。
9. 证据污染必须可检测——不能静默吸收。
10. 污染检测结果必须进入 Decision Trace。
11. Governance 层所有 findings 必须在 Decision Trace 中可追溯。
12. Guardrail block_output 是唯一可终止 Run 的 action。
13. Evaluator 不直接阻止 Candidate 生成。
14. Human Review 不短路剩余评估——系统完成所有检查后再汇聚。
```

---

## 11. 后续 SPEC 依赖

1. SPEC-012：用户私有数据的治理边界（Guardrail 不得访问 user_private 数据）；
2. SPEC-010：MVP 验证指标中的 Governance 指标（Guardrail 触发率、Human Review 触发率等）；
3. SPEC-011：Case Library 与历史案例记忆（Governance 层 findings 进入案例索引）。

---

## 12. 开放问题

1. Guardrail 阈值（如 Interpreted Evidence 占比 40%）是否需要行业调整——**MVP 暂定统一阈值**；
2. Evaluator 是否应引入"历史评分"维度——**MVP 暂不引入**，避免依赖 Case Library；
3. 证据污染检测的 max_depth 默认值——**MVP 暂定 3**，通过 SPEC-005 的 lineage 跟踪深度确定；
4. confidence_cap 叠加是"取最严"还是"累计叠加"——**当前采用取最严**，与 SPEC-006 v0.3.0 §4.5 的叠加语义对齐（各来源叠加）；
5. Human Review 是否应有超时自动降级——**MVP 暂定无超时**，人工复核是终态。

---

## 13. v0.1 总结

SPEC-009 v0.1 定义了 crosslens Governance 层的完整语义。

本版本完成：

1. Governance 三组件架构：Guardrail → Evaluator → Human Review Agg；
2. Guardrail 6 条规则 + 执行决策树 + 边界收窄算法；
3. Evaluator 四维质量检查 + 决策树 + confidence_cap 修改规则；
4. Human-in-the-loop 六来源信号汇聚 + 路由策略；
5. 证据污染检测的递归 lineage 检查算法；
6. Resolved Decision Bounds 完整合并算法；
7. Guardrail Report、Evaluation Report 的完整 schema；
8. Governance 层与 SPEC-003/004/006/007 的接口契约；
9. MVP 实现边界（10 项必须 + 8 项暂不）；
10. 14 条核心不变量。

本版本的核心原则是：

```text
Guardrails narrow bounds, not control flow.
Evaluator checks and flags, never auto-rewrites.
Human review must be aggregated into bounds.
Contamination must be detectable, not silently absorbed.
```

中文表达：

```text
Guardrail 收窄边界，不另开控制流。
Evaluator 检查标记，不自动重写。
人工复核信号必须汇聚到边界。
证据污染必须可检测，不能静默吸收。
```
