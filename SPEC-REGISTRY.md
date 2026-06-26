# SPEC Registry

> 本文件是 CrossLens 规格体系的元数据索引。每个 SPEC 的版本、状态、规范性范围、上下依赖在此统一声明。
>
> 规则：
> - **Approved** 下游只能依赖 **Review** 或 **Approved** 上游。
> - **Review** 下游可依赖 **Review**、**Approved** 或 **Draft** 上游（但依赖 Draft 项在 Approval gate 前必须解除）。
> - 任何 SPEC 变更其 `normative_for` 中声明的枚举、schema 或对象签名时，必须遍历 `consumed_by` 做兼容性检查。
>
> **例外说明：** SPEC-006（Approved）和 SPEC-007（Approved）早于 Registry 规则建立前已先于部分上游通过 Approval。这是有意识的历史先行——两份 SPEC 的枚举/schema/状态机在各自定义域内已稳定，且其上游 SPEC-003/SPEC-004 处于 Review 而非 Draft，语义上满足"上游足够稳定"的意图。后续 SPEC 审批必须严格按上述规则执行。

---

## SPEC 索引

| 编号 | 文件名 | 版本 | 状态 | 文档类型 | 规范性范围 | 可执行 |
|------|--------|------|------|:--------:|------------|--------|
| SPEC-001 | SPEC-001 产品定义与边界 v0.4.md | v0.4 | Draft | 需求 | 产品边界、结构化投研定位、域/Workflow/Playbook 分层、七层架构命名 | — |
| SPEC-002 | SPEC-002 目标用户与核心场景 v0.1.md | v0.1 | Draft | 需求 | 用户画像、场景矩阵、task_type 枚举 (5 values) | — |
| SPEC-003 | SPEC-003 Agentic投研工作流架构 v0.3.4.md | v0.3.4 | Review | 设计 | 核心对象链 (13 objects)、domain 枚举 (5 values)、depth 执行深度、七层职责分层、Evidence Packet schema、Validation Report schema、Conflict Report schema、Decision Candidate schema、Event Log schema | ✅ `executable_specs/spec003/` |
| SPEC-004 | SPEC-004 五类分析能力域与 Analysis Card Schema v0.2.7.md | v0.2.7 | Review | 设计 | Analysis Card schema、domain_status 枚举、stance 枚举、constraint_exports 契约（含 registration_status）、五域能力定义与默认产品角色 | ✅ `executable_specs/spec004/` |
| SPEC-005 | SPEC-005 Capability Package 与 Metric Registry 规范 v0.2.md | v0.2 | Review | 设计 | Metric/Fact/Label Registry schema、Capability Package schema、lineage 追踪、URI 格式规范、confidence 取值规则、resolve_input_ref 算法、Derived Metric 规则表格式 | ✅ `executable_specs/spec005/` |
| SPEC-006 | SPEC-006 Investment Playbook 规范 v0.3.0.md | v0.3.0 | Approved | 设计 | Playbook schema、策略组合层定位、Constraint Evaluation Result schema、OverallResult 枚举 (8 values)、decision_logic 执行语义、confidence_cap 合并、Snapshot hash | ✅ `executable_specs/spec006/` |
| SPEC-007 | SPEC-007 Orchestration 与执行路径 v0.6.md | v0.6 | Approved | 设计 | Run 状态机 (26 states)、Workflow Node schema、路由决策树、域调度、双阶段 Validation、bounds 合并、Cumulative degradation | — |
| SPEC-008 | SPEC-008 Decision Trace 与 Observability v0.1.md | v0.1 | Draft | 设计 | Decision Trace 四层结构、Event Log 汇总、Observability 指标、数据源 lineage 展示 | — |
| SPEC-009 | SPEC-009 Governance Guardrails Evaluator 与人工介入 v0.1.md | v0.1 | Review | 设计 | Guardrail (6 rules)、Evaluator (4 dims)、Human Review aggregation、Resolved Decision Bounds merge、证据污染检测 | ✅ `executable_specs/spec009/` |
| SPEC-010 | SPEC-010 MVP 范围与验证指标 v0.1.md | v0.1 | Draft | 需求 | MVP 范围宪法、depth=deep Full Decision 验证路径、验证标准、交付清单、exclusion 列表 | — |
| SPEC-011 | SPEC-011 Case Library 与历史案例记忆 v0.1.md | v0.1 | Draft | 设计 | Case schema、索引六维、匿名化规则、隐私边界、相似度算法（defined but MVP-deferred） | — |
| SPEC-012 | SPEC-012 数据治理与用户私有数据 v0.1.md | v0.1 | Draft | 需求 | 数据三分类、访问控制决策树、生命周期、删除/导出 | — |
| SPEC-013 | SPEC-013 Fundamentals 域实现规格 v0.2.0.md | v0.2.0 | Review | 实现 | — | — |
| SPEC-014 | SPEC-014 Technical Market 域实现规格 v0.2.3.md | v0.2.3 | Review | 实现 | Part I（§1–§16）Review；Part II（§17–§28）Draft。三层架构 + 高阶扩展、regime 门控、分位自校准 | — |
| SPEC-015 | SPEC-015 Macro Meso 域实现规格 v0.1.1.md | v0.1.1 | Review | 实现 | 消费者域 Pipeline（9 evidence / 7 metric / 3 Context / 9 步）、global_liquidity_metrics evidence、2 个 proposed soft-only metric、§10.2-fallback、market_regime canonical source | — |
| SPEC-016 | SPEC-016 Event Driven 域实现规格 v0.1.0.md | v0.1.0 | Review | 实现 | Event Driven Pipeline（事件发现 / 预期差判断 / 可交易性评分 / 受益链条映射）、runtime score payload-only、PIT/as_of 防泄漏 | — |

---

## 依赖关系（canonical）

```
SPEC-001 (产品定义)
  ├─► SPEC-003 (架构) ──► SPEC-004 (能力域) ──► SPEC-005 (能力包 + Registry)
  │     │                      │                      │
  │     │                      │                      └─► SPEC-013 (Fundamentals 实现)
  │     │                      │                      └─► SPEC-014 (Technical/Market 实现)
  │     │                      │                      └─► SPEC-015 (Macro/Meso 实现)
  │     │                      │                      └─► SPEC-016 (Event Driven 实现)
  │     │                      │
  │     ├─► SPEC-007 (编排) ──► SPEC-008 (Trace)
  │     │                      │
  │     ├─► SPEC-006 (Playbook) ──► SPEC-005
  │     │                      │
  │     └─► SPEC-009 (治理)
  │
  └─► SPEC-010 (MVP) ──► SPEC-011 (案例库) ──► SPEC-012 (数据治理)
```

---

## 文档类型

CrossLens 规格体系采用四类文档分层：

| 类型 | 含义 | 编号范围 | 不详细定义 |
|------|------|---------|-----------|
| **需求** | 产品定位、用户场景、MVP 范围、数据治理 | SPEC-001/002/010/012 | 架构、接口、实现 |
| **设计** | 架构、契约、接口、状态机、治理机制 | SPEC-003~009/011 | 域内部管线、公式、数据源 |
| **实现** | 域内部管线、指标公式、数据源、confidence 模型 | SPEC-013~017 | 开发任务拆解 |
| **任务** | 开发任务拆解、验收标准、依赖关系 | `plan/tasks-*.md`（不进 SPEC 编号） | — |

规则：
- 实现类 SPEC 消费上游设计类 SPEC 的契约，不修改它们。
- 任务类文档不进入 SPEC-REGISTRY，不参与依赖图。
- 如果实现过程中发现设计契约有缺口，应向上游 SPEC 提变更请求，不在实现规格里打补丁。

---

## 规范性枚举（全仓库唯一定义源）

| 枚举 | 定义位置 | 值 |
|------|----------|----|
| `domain` | SPEC-003 §6.1 | `macro_meso`, `fundamentals`, `event_driven`, `sentiment`, `technical_market` |
| `generation_type` | SPEC-003 §6.5 | `computed`, `structured`, `interpreted` |
| `domain_status` | SPEC-004 §10.1 | `completed`, `partial`, `error`, `unavailable` |
| `stance` | SPEC-004 | `positive`, `moderately_positive`, `neutral`, `mixed`, `moderately_negative`, `negative`, `unavailable`, `not_applicable` |
| `OverallResult` | SPEC-006 + `decision_logic.py` | `passed`, `passed_with_caution`, `partially_passed`, `not_passed_for_new_buy`, `not_passed_for_add_position`, `not_suitable_for_playbook`, `need_more_data`, `requires_human_review` |
| `ConstraintStatus` | SPEC-006 + `decision_logic.py` | `pass`, `fail`, `partial`, `insufficient_data`, `stale_data`, `not_applicable`, `error` |
| `allowed_actions` | SPEC-006 + `decision_logic.py` | `buy`, `hold`, `wait`, `avoid`, `reduce`, `add_to_watchlist`, `hold_if_already_owned`, `need_more_data`, `add_position` |
| `domain_status_reason` | SPEC-003 §10.1 + SPEC-004 `models.py` | `insufficient_data`, `skipped_by_config`, `execution_failure`, `data_source_unavailable` |
| `validation_overall_status` | SPEC-003 §13.4 + `models.py` | `passed`, `passed_with_flags`, `blocked`, `error`, `skipped` |
| `validation_severity` | SPEC-003 §13.4 + `models.py` | `block`, `flag`, `note` |

> **全仓库枚举一致性规则：** 任何 SPEC 中使用上述枚举时，必须以本表声明的值域为准。如产品端需要不同 display name（如 "Event Driven / Catalyst"），仅作为 human-facing label，不进入机器枚举。

---

## 规范性 Schema（全仓库唯一定义源）

| Schema | 定义位置 | 规范性格式 |
|--------|----------|------------|
| PlaybookEvaluationReport | SPEC-006 `models.py` | Pydantic v2 + JSON Schema |
| ConstraintEvaluationResult | SPEC-006 `models.py` | Pydantic v2 + JSON Schema |
| ConfidenceCapResult | SPEC-006 `models.py` | Pydantic v2 + JSON Schema |
| Analysis Card | SPEC-004 + `executable_specs/spec004/models.py` | Pydantic v2 + JSON Schema |
| Evidence Packet | SPEC-003 §6.5 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Investment Task | SPEC-003 §6.1 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Asset Info | SPEC-003 §6.1 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Context Bundle | SPEC-003 §6.2 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Context Source | SPEC-003 §6.2 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Analysis Domain Job | SPEC-003 §8 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Post-card Validation Report | SPEC-003 §13 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Conflict Report | SPEC-003 §14 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Decision Candidate | SPEC-003 §18 + `executable_specs/spec003/models.py` | Pydantic v2 + JSON Schema |
| Metric Registry Entry | SPEC-005 §5.2 + `executable_specs/spec005/models.py` | Pydantic v2 + JSON Schema |
| Constraint Export | SPEC-004 + `executable_specs/spec004/models.py` | Pydantic v2 + JSON Schema |
| Data Freshness | SPEC-004 + `executable_specs/spec004/models.py` | Pydantic v2 + JSON Schema |
| Fact Registry Entry | SPEC-005 + `executable_specs/spec005/models.py` | Pydantic v2 + JSON Schema |
| Label Registry Entry | SPEC-005 + `executable_specs/spec005/models.py` | Pydantic v2 + JSON Schema |
| Derived Metric Rule Table | SPEC-005 §15.2 + `executable_specs/spec005/models.py` | Pydantic v2 + JSON Schema |
| Guardrail Report | SPEC-009 + `executable_specs/spec009/models.py` | Pydantic v2 + JSON Schema |
| Evaluation Report | SPEC-009 + `executable_specs/spec009/models.py` | Pydantic v2 + JSON Schema |
| Resolved Decision Bounds | SPEC-009 + `executable_specs/spec009/models.py` | Pydantic v2 + JSON Schema |
| URI Format Spec | SPEC-003 §11 + `docs/uri-resolution.md` | Markdown + Python `uri_resolver.py` |

---

## 可执行规格覆盖

| 包 | 位置 | 覆盖规范 | 状态 |
|----|------|----------|------|
| `crosslens_spec003` | `executable_specs/spec003/` | SPEC-003: InvestmentTask, AssetInfo, ContextBundle, EvidencePacket, AnalysisDomainJob, PostCardValidationReport, ConflictReport, DecisionCandidate, URI resolver | ✅ 已验证 (78 tests) |
| `crosslens_spec006` | `executable_specs/spec006/` | SPEC-006: aggregate_multi_rule, compute_overall_result, resolve_recommended_actions, merge_confidence_cap | ✅ 已验证 (29 tests) |
| `crosslens_spec005` | `executable_specs/spec005/` | SPEC-005: MetricRegistryEntry, FactRegistryEntry, LabelRegistryEntry, DerivedMetricRuleTable | ✅ 已验证 (17 tests) |
| `crosslens_spec004` | `executable_specs/spec004/` | SPEC-004: AnalysisCard, ConstraintExport, DataFreshness, post-card validation rules | ✅ 已验证 (30 tests) |
| `crosslens_spec009` | `executable_specs/spec009/` | SPEC-009: GuardrailReport, EvaluationReport, ResolvedDecisionBounds merge, apply_guardrails, run_evaluator, compute_final_confidence_cap, resolve_decision_bounds, check_evidence_contamination | ✅ 已验证 (59 tests) |

---

## 文件命名规范

- SPEC 文件: `SPEC-{NNN} {Title} v{x.y.z}.md`
  - Title 可使用中英混合，原语种优先（英文标题用英文，中文标题用中文，双语标题中英均可）
  - 文件名不得包含中文标点（`、` `：` `（）`等）；中文部分仅使用中文字符 + 空格
- Canonical 路径以本 Registry 中的 `文件名` 字段为准
- 版本号必须嵌入文件名（如 `v0.3.4`），防止重名歧义

---

## 变更 Checklist

任何人对任何 SPEC 做以下变更时，必须：

1. [ ] 更新本 Registry 中对应 SPEC 的 version
2. [ ] 检查 `normative_for` 中声明的枚举/schema 是否被修改 → 如是，遍历 `consumed_by` 做兼容检查
3. [ ] 若该 SPEC 被 `approved` 状态的 SPEC 依赖，评估是否需要 downgrade 下游状态
4. [ ] 若 README.md 包含派生信息（版本号、状态、链接等），同步更新；如 README 已声明以 Registry 为唯一事实源，则仅确认 Registry → README 的派生链路一致即可
