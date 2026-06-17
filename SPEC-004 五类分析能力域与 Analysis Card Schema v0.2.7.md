# SPEC-004：五类分析能力域与 Analysis Card Schema

**版本：** v0.2.7
**状态：** Review
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4
**文档类型：** 能力域规格 / Analysis Card Schema
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

v0.2.7 合并 SPEC-014 v0.2.2 §10.3 上游变更请求（CR-014-001），为 Technical/Market `domain_payload` 补齐 Part I 实现所需字段，并定义 P4 `key_levels` 的 `[Level]` 对象 schema。状态保持 Review。

主要补齐（来源：SPEC-014 §10.3 / §22.6）：

1. **§37.2** 新增 `KeyLevel` 对象定义与 `key_levels` 根结构；P0–P3 `support`/`resistance` MUST 为 `[]`；P4 起为 `KeyLevel[]`（**Breaking**：v0.2.6 的 `number[]` 示例废弃）；
2. **§37.3** 完整 payload 示例更新：含 `key_levels.source`/`note`、`threshold_calibration` 子对象；
3. **§37.4** `schema_version` 兼容与 Playbook 迁移说明；
4. **§41** 新增 Post-card Validation 规则 #15–#16（`key_levels` 结构与 `threshold_calibration` 对象格式）。

> **CR 追踪：** CR-014-001（`key_levels` + `threshold_calibration`）。`divergence` / `wyckoff` 子对象与 Evidence #7–#13 仍待 SPEC-014 Part I P1/P2 与 Part II 分别提交后续 CR。

v0.2.6 在 v0.2.5 基础上为 `ConstraintExport` 新增治理字段，与 SPEC-005 Metric Registry 治理规则对齐。状态保持 Review。

主要补齐：

1. §9.1 新增 `registration_status`（`registered` / `unregistered_mvp_local` / `proposed`），默认 `registered`，零 breaking change；
2. §9.1 新增 `lineage_constraint_failure`（可选），修复 SPEC-005 §6.2 伪代码引用但模型缺失的存量 bug；
3. §9.2 新增 `registration_status` 与 Hard Constraint 资格的联动规则；
4. executable spec `crosslens_spec004.models.ConstraintExport` 同步更新，Pydantic 校验未注册 export 不得声明 hard 资格。

v0.2.5 在 v0.2.4 基础上将 Company Event derived fact 的生产责任正式归入能力域输出契约，并版本化 Analysis Card 输入契约。状态保持 Review。

> **对齐声明：** SPEC-004 v0.2.5 已与 SPEC-003 v0.3.4 完全对齐。版本号差异仅反映两份文档的独立修订频次——SPEC-003 经历了 4 次微修订（v0.3.1→v0.3.4），而 SPEC-004 通过 v0.2.4+v0.2.5 两次集中修订批处理了与 SPEC-003 v0.3.4 的所有互操作接口。§4、§7、§44、§47 等关键章节均已显式引用 SPEC-003 v0.3.4 的对应规则。

主要补齐：

1. §25.1 新增 `event_resolution_status` 枚举；
2. §26.2 定义三个事件类 derived facts 的计算、缺失与导出规则；
3. 明确 derived facts 通过必填 boolean `fact_value` 表达真假、仅支撑 Soft Constraint，来源属性不足时不得以 `false` 代替未知；
4. Analysis Card 新增必填 `schema_version`，消费者必须执行版本兼容检查。

v0.2.4 在 v0.2.3 基础上补齐 SPEC-006 默认 Hard Constraint 的辅助控制接口。状态保持 Review。主要补齐：

1. Fundamentals Computed Evidence 新增 boolean metric `growth_capex_flag`；
2. §20 将 `metric://growth_capex_flag` 注册为可支撑 Hard Constraint 的 computed export；
3. 明确该 flag 必须由公司级资本开支与增长指标确定性计算，不得直接由宏观 `capex_cycle_stage` label 推断。

v0.2.3 在 v0.2.2 基础上微修订。状态保持 Review。主要补齐：

1. **P0** `value_path` 根节点歧义修正 → 去掉 `metrics.` 前缀，根节点明确定义为 Evidence Packet.`metrics` 字典（§9.3 + §4.1 全例更新）；
2. **P0** 禁止 `completed + unavailable` 矛盾组合（§5.3 + §41）；
3. **P0** `time_horizon_mismatch` 触发条件精确化：bucket 跨 ≥2 级 或 days 差 >90（§44）；
4. **P1** §26.1 lineage 链式传播局限显式承认（§26.1 NOTE）；
5. **P1** `valid_until` quarterly 推导规则明确化：最近的下一个季末后推 45 天（§4.3）；
6. **P1** Macro/Meso 长期 `partial` 为 MVP 预期行为，不阻塞 Decision Candidate 生成（§16）；
7. **P2** §41 `mixed` stance 纳入 opposing_evidence 强制范围；§47 Q5 标为 P1；§46 补 SPEC-007；§0 版本说明语义补全。

v0.2.2 在 v0.2.1 基础上微修订。状态由 Draft 升级为 Review。主要补齐：

1. **P0** `domain_status → stance` 映射约束（§8.3）：阻止矛盾组合；
2. **P0** `constraint_exports` 的 `value_path` 根节点与 label 引用语法说明（§9.1）；
3. **P0** `source_event_generation_type` 来源归属澄清（§26.1 + SPEC-003 同步需求）；
4. **P1** `valid_until` 推导逻辑补充（§4.3 参考表）；
5. **P1** `missing_required_evidence` 来源基准说明（§45）；
6. **P2** Sentiment `sentiment_vs_valuation` 冲突归属修正（§33 → §21，原因见 §2.2 能力域隔离原则：Sentiment 不持有估值数据）；
7. **P2** 关闭开放问题 #1（confidence 跨域比较）和 #4（Sentiment 权重提升）；
8. 小修：stance 反方证据覆盖范围、confidence 降幅默认值、evidence_ref 无效处理、总结措辞。

v0.2.1 在 v0.2 基础上微修订。不改变能力域设计，只补齐 schema 精度缺口：

1. **P0** constraint_exports 改为多态结构（§9.1）：同时容纳 `metric` / `fact` / `label`，新增 `export_type`、`export_ref`、`allowed_constraint_types`；
2. **P1** Company Event 四个 Computed metrics 增加 lineage 约束（§26.1）：必须 `source_event_certainty = confirmed` 且非 Interpreted Evidence；
3. **P1** `data_freshness` 从"可选但推荐"升级为条件必填（§4.3）：`domain_status ∈ {completed, partial}` 且 `constraint_exports` 非空时必填；
4. **P1** `time_horizon` 增加标准化字段（§4.4）：`time_horizon_bucket` / `time_horizon_days_min` / `time_horizon_days_max`；
5. **P2** Company Event 增加 `event_type` 枚举 allowlist（§25.1）。

v0.2 合并 SPEC-004 v0.1 初稿与 v0.1.1 微补丁。主要收紧：

1. Fundamentals 降级规则对齐 SPEC-003 最小分析阈值；
2. Company Event / Catalyst 的 Hard Constraint 出口收紧；
3. Macro / Meso 增加 `macro_regime_vs_playbook` 冲突；
4. 各能力域 `domain_payload` 增加枚举 allowlist；
5. Conflict Detection 对 Flag Card 的处理对齐 SPEC-003；
6. Analysis Card 增加 `data_freshness`；
7. 增加跨域 `time_horizon_mismatch` 通用冲突规则；
8. ~~关闭 Company Event 官方公告事件标签支撑 Hard Constraint 的 MVP 开放问题~~ — **v0.2 已关闭：不能**。

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
  "schema_version": "SPEC-004@0.2.5",
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
  "time_horizon_bucket": "medium_term",
  "time_horizon_days_min": 180,
  "time_horizon_days_max": 365,
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
      "export_type": "metric",
      "export_ref": "metric://revenue_growth_ttm",
      "evidence_ref": "ev_financial_001",
      "value_path": "revenue_growth_ttm",
      "determinism_level": "computed",
      "can_support_hard_constraint": true,
      "allowed_constraint_types": ["hard", "soft"]
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
| `schema_version` | Analysis Card Schema 版本；格式为 `SPEC-004@<semver>` |
| `task_id` | 对应 Investment Task |
| `run_id` | 对应本次分析运行 |
| `domain` | 能力域名称 |
| `domain_status` | 能力域执行状态 |
| `summary` | 简短结论 |
| `stance` | 能力域立场 |
| `confidence` | 能力域自评置信度 |
| `confidence_reason` | 置信度来源说明 |
| `time_horizon` | 判断适用周期（自然语言表述） |
| `time_horizon_bucket` | 周期分桶：`intraday` / `short_term` / `medium_term` / `long_term` / `unknown`（v0.2.1 新增） |
| `time_horizon_days_min` | 适用周期最短天数（v0.2.1 新增） |
| `time_horizon_days_max` | 适用周期最长天数（v0.2.1 新增） |
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

> v0.2 新增字段。v0.2.1 升级为条件必填。

`data_freshness` 为可选但强烈推荐字段。

**条件必填规则：** 当 Analysis Card 同时满足以下条件时，`data_freshness` 必填：

1. `domain_status = completed` 或 `partial`；
2. `constraint_exports` 非空（即该 Card 有可被 Playbook 引用的导出项）。

若 `constraint_exports` 非空但 `data_freshness` 缺失，Playbook Evaluation 应将其 `staleness_risk` 视为 `unknown`，并在 Decision Trace 中标记。

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

>`valid_until` 的推导逻辑（v0.2.2 新增）：
>
>| freshness_level | 推荐默认 `valid_until` 算法 |
>|---|---|
>| real_time | `as_of + 1 天` |
>| intraday | `as_of + 1 天` |
>| daily | `as_of + 1 天` |
>| quarterly | `as_of` 日期之后最近的下一个季末（3/31、6/30、9/30、12/31）后推 45 天 |
>| event_based | 无默认 TTL，由能力域根据事件类型赋值 |
>| static | 无 TTL |
>
>以上为推荐默认值。具体 TTL 可由 Run Config 覆盖。

### 4.4 time_horizon 标准化

> v0.2.1 新增。与 §44 跨域 time_horizon_mismatch 冲突规则配套。

`time_horizon` 保留自然语言字段供 Agent 和人类阅读，同时增加三个机器可读字段：

| 字段 | 含义 |
|---|---|
| `time_horizon_bucket` | 标准化周期分桶 |
| `time_horizon_days_min` | 适用周期最短天数（整数） |
| `time_horizon_days_max` | 适用周期最长天数（整数） |

`time_horizon_bucket` 枚举：

```text
intraday       （< 5 天）
short_term     （5 天 - 3 个月）
medium_term    （3 个月 - 1 年）
long_term      （> 1 年）
unknown
```

Conflict Detection 使用 `time_horizon_bucket` 或 `time_horizon_days_*` 判断时间周期是否"相差一个数量级以上"（§44），而非解析自然语言字符串。

---

## 5. domain_status

### 5.1 枚举

```text
completed
partial
error
unavailable
```

### 5.2 语义

| domain_status | 含义 | 是否计入最小可用卡片阈值 |
|---|---|---|
| `completed` | 能力域正常完成分析 | 是 |
| `partial` | 部分完成，但存在数据缺口或低置信度 | 是，但需降权 |
| `error` | 能力域执行失败 | 否 |
| `unavailable` | 数据不可用，无法形成有效分析 | 否 |

### 5.3 domain_status 与 data_quality 的关系

`domain_status` 和 `data_quality` 是正交字段。

`domain_status` 描述能力域是否完成任务。
`data_quality` 描述输入数据质量。

可能组合示例：

| domain_status | data_quality | 含义 |
|---|---|---|
| completed | high | 能力域完成，数据质量高 |
| completed | medium | 能力域完成，数据质量一般 |
| completed | low | 能力域完成，但数据质量差 |
| partial | high | 数据质量高，但覆盖不完整 |
| partial | medium | 数据质量一般，覆盖不完整 |
| partial | low | 数据质量差，覆盖不完整 |
| unavailable | unavailable | 关键数据不可用 |
| unavailable | unknown | 数据不可用，未评估数据质量 |
| error | unknown | 执行失败，无法判断数据质量 |

**禁止组合：** `completed + unavailable`。若能力域报告 `domain_status = completed`，说明分析已完成——此时不应该声称数据完全不可用。若所有输入数据均为不可用，应报告 `unavailable` 或 `error`。Post-card Validation 必须将 `completed + unavailable` 标记为 `block`。

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
| unavailable | 0.25 |
| error | null 或 0 |

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
unavailable
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
| unavailable | 数据不可用 |
| not_applicable | 该能力域不适用于当前任务 |

MVP 阶段 Analysis Card 不使用 `strong_positive` 或 `strong_negative`，避免能力域层面过度表达。

### 8.3 domain_status → stance 约束

> v0.2.2 新增。防止 `domain_status` 与 `stance` 的矛盾组合。

`domain_status` 对 `stance` 的合法取值有硬约束：

| domain_status | 合法 stance |
|---|---|
| completed | positive / moderately_positive / neutral / mixed / moderately_negative / negative |
| partial | positive / moderately_positive / neutral / mixed / moderately_negative / negative / unavailable |
| unavailable | unavailable |
| error | not_applicable（或 null） |

若 `domain_status = completed` 但 `stance = unavailable`，Post-card Validation 必须将其标记为 `block`。

该约束同时纳入 §41 质量检查规则。

---

## 9. constraint_exports

`constraint_exports` 用于告诉 Playbook Evaluation：该 Analysis Card 中哪些指标或事实可以被 Constraint 引用。

### 9.1 多态结构

> v0.2.1 更新：原最小结构仅支持 metric_ref，现改为多态，同时容纳 metric、fact、label。

```json
{
  "export_type": "metric",
  "export_ref": "metric://revenue_growth_ttm",
  "evidence_ref": "ev_financial_001",
  "value_path": "revenue_growth_ttm",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "allowed_constraint_types": ["hard", "soft"],
  "registration_status": "registered"
}
```

未注册 MVP 本地 export 示例（soft-only）：

```json
{
  "export_type": "metric",
  "export_ref": "metric://divergence_strength",
  "evidence_ref": "ev_tm_div_001",
  "value_path": "divergence_strength",
  "determinism_level": "computed",
  "can_support_hard_constraint": false,
  "allowed_constraint_types": ["soft"],
  "registration_status": "unregistered_mvp_local"
}
```

Lineage 降级示例（已注册 metric，但 lineage 不满足 → soft-only）：

```json
{
  "export_type": "metric",
  "export_ref": "metric://post_event_1d_return",
  "evidence_ref": "ev_event_001",
  "value_path": "post_event_1d_return",
  "determinism_level": "computed",
  "can_support_hard_constraint": false,
  "allowed_constraint_types": ["soft"],
  "registration_status": "registered",
  "lineage_constraint_failure": "source_event_not_confirmed"
}
```

Fact 示例：

```json
{
  "export_type": "fact",
  "export_ref": "fact://retail_sentiment_overheated",
  "fact_value": true,
  "evidence_ref": "ev_sentiment_001",
  "determinism_level": "structured",
  "can_support_hard_constraint": false,
  "allowed_constraint_types": ["soft"]
}
```

Label 示例：

```json
{
  "export_type": "label",
  "export_ref": "label://industry_cycle_stage",
  "label_value": "early_recovery",
  "evidence_ref": "ev_industry_cycle_001",
  "determinism_level": "structured",
  "can_support_hard_constraint": false,
  "allowed_constraint_types": ["soft"]
}
```

| 字段 | 含义 |
|---|---|
| `export_type` | `metric` / `fact` / `label` |
| `export_ref` | Playbook Constraint 引用的实体 URI |
| `fact_value` | 仅 `export_type = fact` 时必填，boolean |
| `label_value` | 仅 `export_type = label` 时必填，枚举值 |
| `evidence_ref` | 底层 Evidence Packet 引用 |
| `value_path` | 仅 `export_type = metric` 时必填 |
| `determinism_level` | `computed` / `structured` / `interpreted` |
| `can_support_hard_constraint` | 是否可支撑 Hard Constraint |
| `allowed_constraint_types` | 该 export 可用于哪种约束类型（`hard` / `soft` / 两者） |
| `registration_status` | 治理状态：`registered`（已在 SPEC-005 Registry 登记，默认）/ `unregistered_mvp_local`（域内扩展、未注册）/ `proposed`（已提交 Registry 变更请求）。详见 SPEC-005 §6.4 |
| `lineage_constraint_failure` | 可选。已注册 metric 因 lineage 约束不满足而降级为 soft-only 时的原因码 |

### 9.2 规则

1. `can_support_hard_constraint = true` 的 export 必须来自 Computed Evidence；
2. Structured Evidence 可以导出 metric，但默认 `can_support_hard_constraint = false`；
3. Interpreted Evidence 不得导出可支撑 Hard Constraint 的 metric；
4. facts 默认只能支撑 Soft Constraint；
5. 所有 export 必须保留 evidence_ref；
6. 若 evidence_ref 无法追溯，该 export 项应被 Post-card Validation 移除，并在对应 Analysis Card 的 `warnings` 中记录。
7. `export_type = fact` 时必须显式提供 boolean `fact_value`；fact 不得通过“export 是否存在”隐式表达真假。
8. **`registration_status` 治理规则（与 SPEC-005 §6.4 对齐）：**
   - `registration_status = "registered"`（默认）：按 metric 定义决定 `can_support_hard_constraint` 和 `allowed_constraint_types`；
   - `registration_status ∈ {"unregistered_mvp_local", "proposed"}`：**MUST** `can_support_hard_constraint = false`，**MUST** `allowed_constraint_types = ["soft"]`；
   - Playbook Evaluation **MUST** 拒绝任何 `registration_status != "registered"` 的 export 被 Hard Constraint 引用；
   - Pydantic 模型（`crosslens_spec004.models.ConstraintExport`）在构造时强制校验上述不变量。
9. `lineage_constraint_failure` 非空时，表示已注册 metric 因 lineage 不满足而主动降级；此时 `can_support_hard_constraint` 应为 `false`，`registration_status` 仍为 `registered`。

### 9.3 value_path 寻址规则

> v0.2.2 新增。

`value_path` 的根节点是对应 Evidence Packet 的 `metrics` 字典。

```text
evidence_ref → Evidence Packet → .metrics → .{value_path}
```

示例：`"evidence_ref": "ev_financial_001"` + `"value_path": "revenue_growth_ttm"` → 解析为 `ev_financial_001.metrics.revenue_growth_ttm`。

若 `export_type = fact`，无 `value_path`，Playbook Constraint 通过 `export_ref` 的 `fact://` URI 引用事实标签（如 `fact://retail_sentiment_overheated`），并读取 boolean `fact_value`。判断规则由 SPEC-006 Playbook 规范定义。

若 `export_type = label`，`label_value` 携带枚举值，Playbook Constraint 通过 `export_ref` 引用该 label 实体，并使用比较表达式（如 `!= downtime`）判断 `label_value`。完整 label constraint 引用语法由 SPEC-006 定义。

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

Structured labels 默认只能支撑 Soft Constraint。若未来需要 conditional_hard_constraint，必须由 SPEC-006 Playbook 或 SPEC-009 Governance 显式声明，且该 export 仍不得设置 `can_support_hard_constraint = true`。

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

> **MVP 预期行为（v0.2.3 新增）：** Macro / Meso 在 MVP 阶段长期处于 `partial` 或 `data_quality = low/medium` 是预期行为，并非系统故障。此时能力域不应阻塞 Decision Candidate 生成（与 §22 Fundamentals 的 `unavailable / error → analysis_incomplete` 逻辑相反）。若 Macro/Meso 的唯一贡献是背景信息，用户可在 Decision Trace 中看到该能力域的输出质量标记，但不影响 Playbook Evaluation 主流程。

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
    "growth_capex_flag": true,
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
12. `metric://fcf_yield`；
13. `metric://growth_capex_flag`。

这些 metrics 必须来自 Computed Evidence。

`growth_capex_flag` 为 boolean metric，仅在公司级资本开支增长、产能建设进度和对应增长投入满足 Metric Registry 的确定性计算规则时设为 `true`。不得仅根据 Macro / Meso 的 `capex_cycle_stage` Structured label 推断该值。其 `constraint_exports` 必须声明：

```json
{
  "export_type": "metric",
  "export_ref": "metric://growth_capex_flag",
  "evidence_ref": "ev_financial_001",
  "value_path": "growth_capex_flag",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "allowed_constraint_types": ["hard", "soft"]
}
```

---

## 21. Fundamentals 常见冲突类型

| 冲突类型 | 示例 | 默认严重度 |
|---|---|---|
| fundamentals_vs_valuation | 增长强但估值过高 | medium |
| **sentiment_vs_valuation** | **估值高且市场情绪极热，形成追高风险** | **high** |
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
3. 若 Fundamentals Card `domain_status = unavailable` 或 `error`，默认输出 `analysis_incomplete`；
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
  "domain": "company_event",
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
  "domain": "company_event",
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

#### event_resolution_status

```text
open
resolved
not_applicable
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

#### event_type

> v0.2.1 新增。`event_list[].event_type` 必须使用以下枚举，不允许 Agent 自由发明。

```text
earnings_release
guidance_change
management_change
product_launch
major_order
regulatory_event
litigation_event
mna_event
supply_chain_event
capital_return_event
credit_event
unknown
```

### 25.2 完整 payload

```json
{
  "event_list": [
    {
      "event_type": "guidance_change",
      "event_date": "2026-06-14",
      "event_direction": "positive",
      "event_materiality": "high",
      "event_certainty": "confirmed",
      "event_resolution_status": "open",
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

`event_date` 使用 ISO 8601 日期或时间戳。需要导出 `latest_material_event_is_confirmed` 时，所有参与“最新事件”比较的 high materiality 事件必须具有可解析的 `event_date`。`event_resolution_status` 缺失不会使整张 Card 无效，但会使依赖该属性的 derived fact 按 §26.2 省略。

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

### 26.1 Computed Event Metrics 的 lineage 约束

> v0.2.1 新增。

以下四个 Computed Event metrics 依赖底层事件识别。若底层事件来自低置信度或不可靠来源，这些 metrics 同样被污染。

因此，Computed Event metrics 只有在以下条件**全部**满足时，才可设 `can_support_hard_constraint = true`：

1. 该 metric 的 source event 可追溯（`source_event_ref` 有效）；
2. source event 的 `event_certainty = confirmed`；
3. source event 的生成类型非 `Interpreted Evidence`。

若任一条件不满足，该 metric 必须降级为 `can_support_hard_constraint = false`，`allowed_constraint_types` 降低至 `["soft"]`，或标记为 `conditional_hard_constraint`。

```json
{
  "export_type": "metric",
  "export_ref": "metric://days_since_event",
  "evidence_ref": "ev_event_timing_001",
  "value_path": "days_since_event",
  "determinism_level": "computed",
  "can_support_hard_constraint": true,
  "allowed_constraint_types": ["hard", "soft"],
  "source_event_ref": "ev_event_001",
  "source_event_certainty": "confirmed",
  "source_event_generation_type": "structured"
}
```

>`source_event_generation_type` 字段说明（v0.2.2 新增）：该字段的值来自 source event 对应 Evidence Packet 的 `generation_type` 字段（定义见 SPEC-003 §7）。SPEC-004 不新增 Evidence Packet schema 字段；此字段由 Company Event 能力域在生成 `constraint_exports` 时从底层 Evidence 读取并透传。建议 SPEC-003 同步在 Computed Event Metric Evidence Packet 示例中增加对 source event 的 lineage 引用。

>**已知局限（v0.2.3 新增，v0.2.3 修正归属）：** 当前 lineage 约束仅检查 source event 的直接 Evidence Packet。若 source event 本身引用了一个 Interpreted Evidence 作为其输入（例如，一个"结构化"事件标签是由 LLM 解释步骤生成的），SPEC-004 层面无法检测这种间接污染。完整的 lineage 递归检查应交由 SPEC-005（Capability Package 工具调用链 lineage）与 SPEC-009（Governance 层证据污染检测）协同实现。

### 26.2 事件类 derived fact 导出规范

Company Event / Catalyst 能力域是以下 derived fact 的生产者。它们必须在 Analysis Card 生成阶段基于结构化 `event_list` 确定性导出；Playbook Evaluation 不得自行重建或猜测这些事实。

| `export_ref` | `fact_value = true` | `fact_value = false` |
|---|---|---|
| `fact://any_material_event_low_certainty` | 存在至少一条 `event_materiality = high`，且 `event_certainty ∈ {partially_confirmed, rumor, unknown}` | 至少存在一条 high materiality 事件，且所有此类事件均为 `confirmed` |
| `fact://latest_material_event_is_confirmed` | 按 `event_date` 选出的最新一条 `event_materiality = high` 事件，其 `event_certainty = confirmed` | 最新一条 high materiality 事件的 certainty 明确为 `partially_confirmed` 或 `rumor` |
| `fact://any_material_negative_event_unresolved` | 存在至少一条 `event_materiality = high`、`event_direction = negative` 且 `event_resolution_status = open` 的事件 | 至少存在一条 high materiality negative 事件，且所有此类事件均为 `resolved` 或 `not_applicable` |

导出要求：

1. `export_type = fact`；
2. `determinism_level = structured`；
3. `can_support_hard_constraint = false`；
4. `allowed_constraint_types = ["soft"]`；
5. `evidence_ref` 必须指向 derived-fact Evidence Packet；该 Packet 的 lineage 必须包含全部参与判定的 source event refs；
6. 只有满足表中明确的 true 或 false 条件时才允许导出。所需属性缺失、无法选择“最新事件”，或遇到表中未定义为 true 的 `unknown` 时，必须省略受影响的 export，并在 `warnings` 中记录原因；
7. `event_list` 为空时不导出上述 facts，不得把“无数据”解释为 `false`；
8. `latest_material_event_is_confirmed` 要求候选事件具有机器可解析的 `event_date`。并列日期按 `source_evidence_ref` 字典序稳定选择，并在 Analysis Card `warnings` 中记录并列情况。

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

1. `domain_status = partial` 或 `unavailable`；
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
| sentiment_vs_event | 情绪负面但公司事件正面 | medium |
| sentiment_vs_technical | 情绪过热但价格趋势仍强 | medium |
| sentiment_data_noise | 情绪数据低质量 | low |

> **注意：** `sentiment_vs_valuation` 冲突实际是跨域冲突（Sentiment ∩ Fundamentals Valuation）。该冲突类型由 Conflict Detection 节点处理，Fundamentals 侧记录为 `fundamentals_valuation_vs_sentiment`（§21）。按照 §2.2 的能力域隔离原则，Sentiment 能力域不持有估值数据，因此不在本表中直接记录。

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

### 37.2 key_levels 与 KeyLevel 对象

> v0.2.7 新增（CR-014-001，对齐 SPEC-014 §10.1 / §22.6）。

#### KeyLevel 对象（P4+）

当 `support_resistance_metrics` 成功计算（SPEC-014 Feature D，P4）时，`support` / `resistance` 数组元素 MUST 为下列对象，**不得**再使用 v0.2.6 及更早版本的纯数值 `number[]`：

```json
{
  "price": 12.30,
  "strength": 0.72,
  "source": "volume_poc",
  "touches": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `price` | number | ✅ | 价位（> 0） |
| `strength` | number | ✅ | 综合强度 0.0–1.0（SPEC-014 §22.5） |
| `source` | string | ✅ | 来源：`volume_poc` / `swing_pivot` / `hvn` / `lvn` / `integer_level` / `ma_confluence` 等 |
| `touches` | integer | ✅ | 触及次数（≥ 0；POC 等非枢轴源可为 0） |

#### key_levels 根对象

```json
{
  "support": [],
  "resistance": [],
  "source": "none",
  "note": "MVP 不交付支撑/阻力自动计算（SPEC-014 P0–P3）",
  "poc": null,
  "value_area": null
}
```

| 字段 | 类型 | 阶段 | 说明 |
|---|---|:---:|---|
| `support` | `KeyLevel[]` | P0+ | P0–P3 **MUST** 为 `[]`；P4 启用 Feature D 后可为非空 |
| `resistance` | `KeyLevel[]` | P0+ | 同上 |
| `source` | string | P0+ | `"none"` 或 `"support_resistance_metrics"` |
| `note` | string | P0+ | `source="none"` 时 MUST 说明置空原因 |
| `poc` | number \| null | P4 | 成交量控制点；未计算时为 `null` |
| `value_area` | `[number, number]` \| null | P4 | 价值区 `[low, high]`；未计算时为 `null` |

> **Breaking Change（相对 v0.2.6）：** §37.2 旧示例 `support: [120, 112]`（纯数值数组）**已废弃**。Post-card Validation 见 §41 #15。

#### threshold_calibration 子对象

> v0.2.7 新增（CR-014-001）。v0.2.6 及更早若使用字符串 `"uncalibrated"`，Post-card Validation = `block`（§41 #16）。

```json
{
  "part_i": "uncalibrated",
  "part_ii": null
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `part_i` | `"uncalibrated"` \| `"self_calibrated"` | Part I（Layer 1–3）阈值校准状态（SPEC-014 §10.1） |
| `part_ii` | `null` \| `"self_calibrated_percentile"` | Part II 高阶功能；P0–P2 为 `null`，P3+ 为 `"self_calibrated_percentile"` |

### 37.3 完整 payload（P0–P3 示例）

```json
{
  "trend_state": "uptrend",
  "momentum_state": "positive_but_extended",
  "volume_state": "above_average",
  "volatility_state": "normal",
  "liquidity_state": "sufficient",
  "key_levels": {
    "support": [],
    "resistance": [],
    "source": "none",
    "note": "MVP 不交付支撑/阻力自动计算。trading_range 软参考见 wyckoff 子对象（SPEC-014 §10.1）",
    "poc": null,
    "value_area": null
  },
  "threshold_calibration": {
    "part_i": "uncalibrated",
    "part_ii": null
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

### 37.4 P4 key_levels 扩展示例（Feature D 启用后）

```json
{
  "key_levels": {
    "support": [
      {"price": 12.30, "strength": 0.72, "source": "volume_poc", "touches": 0}
    ],
    "resistance": [
      {"price": 14.10, "strength": 0.65, "source": "swing_pivot", "touches": 3}
    ],
    "source": "support_resistance_metrics",
    "note": "",
    "poc": 13.05,
    "value_area": [12.50, 13.80]
  }
}
```

### 37.5 schema_version 兼容与 Playbook 迁移

| 消费者 | v0.2.6 行为 | v0.2.7 要求 |
|---|---|---|
| Post-card Validation（§41 #15–#16） | 允许 `number[]` key_levels；无 `threshold_calibration` 对象 | `KeyLevel[]` 或空数组；`threshold_calibration` 必须为对象 |
| Playbook soft 规则 | 可能引用 `key_levels.support[0]` 为数值 | MUST 改为 `support[0].price`，或消费 `metric://nearest_support`（SPEC-014 §25.2，P4 注册后） |
| Conflict Detection（§42） | 不直接读 `key_levels` | 无变更 |
| Decision Trace | payload 快照 | 识别新结构；无 block 风险 |

Analysis Card `schema_version` SHOULD bump 至 `SPEC-004@0.2.7`（或更高）以声明消费者已支持本节 schema。旧版 Card 若仍含 `number[]`，Validation = `block`，并在 `warnings` 记录 `legacy_key_levels_format`。

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

1. `domain_status = unavailable` 或 `partial`；
2. 不支撑择时判断；
3. 不应输出趋势确认；
4. 不应影响长期基本面 Playbook 的核心判断；
5. 可以进入 Decision Trace 说明数据缺失。

---

## 41. 能力域质量检查规则

每张 Analysis Card 必须通过以下基础检查：

1. 必须包含 `card_id`、`schema_version`、`task_id`、`run_id`、`domain`；
2. 必须包含合法 `domain_status`；
3. 必须包含合法 `data_quality`；
4. `confidence` 必须符合上限规则；
5. 若 `domain_status = completed`，必须至少有一个 supporting_evidence 或 opposing_evidence；
6. 所有 supporting_evidence 和 opposing_evidence 必须能追溯到 Evidence Packet；
7. 若 `stance ∈ {positive, moderately_positive, mixed, negative, moderately_negative}`，必须包含 opposing_evidence。其中 `mixed` 立场语义上意味着同时存在正面和负面信号——缺少 opposing_evidence 的 `mixed` 自相矛盾；
8. 若 `data_quality = low`，必须包含 warnings；
9. 如果有 constraint_exports，必须明确 determinism_level 和 can_support_hard_constraint；
10. 不允许未引用证据的重大判断；
11. 若 `constraint_exports` 中存在 `can_support_hard_constraint = true` 的 export 且 `data_freshness` 字段缺失，Post-card Validation = `block`；
12. 若 `constraint_exports` 仅包含 soft export 且 `data_freshness` 字段缺失，Post-card Validation = `flag`。
13. `schema_version` 必须是消费者明确支持的版本，或存在已注册的向后兼容适配器；缺失或不兼容时不得静默按当前版本解释。
14. `export_type = fact` 时必须存在 boolean `fact_value`；缺失或类型错误时移除该 export，并在 `warnings` 中记录。
15. Technical/Market `domain_payload.key_levels`（v0.2.7+，§37.2）：`support` / `resistance` 每项 MUST 为 `KeyLevel` 对象或数组为空。若元素为纯 `number`（v0.2.6 旧格式）→ Post-card Validation = `block`，`warnings` 追加 `legacy_key_levels_format`。P0–P3 实现（SPEC-014 Part I）MUST 输出 `support=[]`、`resistance=[]`、`source="none"` 及说明性 `note`。
16. Technical/Market `domain_payload.threshold_calibration`（v0.2.7+，§37.2）MUST 为 `{part_i, part_ii}` 对象；字符串格式 → Post-card Validation = `block`。

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

> v0.2 新增。v0.2.3 精确化触发算法。

**触发条件（v0.2.3 精确化，v0.2.3 修正条件 2 歧义）：** 以下任一条件满足时，标记 `time_horizon_mismatch`：

1. 两个能力域的 `time_horizon_bucket` 相差 ≥ 2 个等级（例如 `short_term` vs `long_term`）；
2. 两个能力域的中值天数差 > 90 天（中值 = `(time_horizon_days_min + time_horizon_days_max) / 2`），且不满足条件 1。

条件 1 和条件 2 共同覆盖两种不同的错配模式——条件 1 捕捉 bucket 级别的明显分类错配（如 short_term vs long_term），条件 2 捕捉同一 bucket 分类下或相邻 bucket 间超出预期范围的实际天数跨度错配（如 medium_term 内两个域的实际周期差 > 90 天）。条件 2 的"且不满足条件 1"确保条件 1 优先触发，避免重复标记。

两个条件均基于机器可读字段（`time_horizon_bucket` / `time_horizon_days_*`），不依赖自然语言字符串解析。具体阈值 90 天为 MVP 默认值，可由 SPEC-007 Orchestration 配置覆盖。

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
3. 可轻微降低 confidence_cap（默认降低 0.05，可由 Run Config 配置）；
4. 必须进入 Decision Trace；
5. Decision Trace 应说明：该冲突是周期不一致，不一定是方向冲突。

例外：如果 Playbook 明确允许多周期综合判断，则 `time_horizon_mismatch` 可以降级为 Note。

> **NOTE（v0.2.3）：** Technical / Market 的 `time_horizon_bucket` 赋值策略暂定为由分析任务的 Playbook 目标周期决定。该策略为占位默认值，待 §47 Q5（投资型 vs 交易型技术分析区分）关闭后更新。

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

各能力域应在初始化时声明其 required Evidence Packet 类型列表。若声明的 required 项在本次运行中缺失，对应缺失项进入 `evidence_coverage.missing_required_evidence`，并可能导致 `domain_status = partial` 或 `unavailable`。

> 其他能力域的 MVP 实现边界统一见本节。Macro/Meso 的 MVP 范围额外定义见 §11.3。

---

## 46. 后续 SPEC 依赖

SPEC-004 依赖和影响以下文档：

1. SPEC-003：Agentic 投研工作流架构；
2. SPEC-005：Capability Package 规范；
3. SPEC-006：Investment Playbook 规范；
4. SPEC-007：Orchestration 与执行路径；
5. SPEC-008：Decision Trace 与 Observability；
6. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
7. SPEC-010：MVP 范围与验证指标；
8. SPEC-011：Case Library 与历史案例记忆；
9. SPEC-012：数据治理与用户私有数据。

---

## 47. 开放问题

1. ~~Analysis Card confidence 是否需要统一算法~~ — **v0.2.2 已关闭：MVP 阶段 confidence 为能力域自评，不跨域比较**。Conflict Detection 和 Playbook Evaluation 使用 `data_quality` + `domain_status` 组合判断可信度，而非直接比较 confidence 数值。统一算法留待 SPEC-005 或 SPEC-009 定义；
2. Metric Registry 应归入 SPEC-005 还是 SPEC-006；
3. ~~Company Event 的官方公告事实能否支撑 Hard Constraint~~ — **v0.2 已关闭：不能**；
4. ~~Sentiment 是否应在某些短线 Playbook 中提升权重~~ — **v0.2.2 已关闭：Sentiment 的权重提升不在 SPEC-004 层面实现**。能力域设计保持不变，权重调整由 Playbook 在 Soft Constraint 层面声明（SPEC-006）；
5. Technical / Market 是否需要区分投资型技术分析与交易型技术分析（**P1** — 直接影响 §44 `time_horizon_mismatch` 规则和 `time_horizon_bucket` 赋值策略）；
6. Macro / Meso 是否需要单独的行业供需模型扩展文档；
7. ~~Analysis Card 是否需要版本化 schema。~~ 已在 v0.2.5 关闭：`schema_version` 为必填字段，消费者必须执行兼容检查。

---

## 48. v0.2.5 总结

SPEC-004 v0.2.5 定义了五类分析能力域与 Analysis Card Schema。

本版本完成以下约束：

1. 能力域不是 Agent，而是能力边界；
2. 能力域之间不得直接相互调用；
3. 每个能力域只读取 Context Bundle、Evidence Packets 和 Playbook Constraints；
4. 每个能力域只向编排器返回 Analysis Card；
5. Analysis Card 是结构化投研判断单元；
6. Analysis Card 通过必填 `schema_version` 建立机器可读的兼容契约；
7. domain_status 与 data_quality 正交；
8. domain_status 对 stance 有硬约束映射；
9. confidence 是能力域自评置信度，受双重 cap 约束，MVP 阶段不跨域比较；
10. constraint_exports 多态化（metric / fact / label），含 value_path 寻址规则和 label 引用语法；
11. Fundamentals 是 MVP 中最主要的 Hard Constraint 来源；
12. Sentiment 默认降权，不支撑 Hard Constraint；
13. Macro / Meso 在 MVP 中主要提供背景和风险约束；
14. Technical / Market 可支撑部分风险和择时约束，但不单独支撑长期买入；
15. Company Event / Catalyst 事件标签一律不支撑 Hard Constraint，仅 4 个 Computed metrics 在满足 lineage 约束（source_event 已确认 + 非 Interpreted）时可支撑；
16. Company Event / Catalyst 负责导出三个仅供 Soft Constraint 使用的事件类 derived facts；
17. 各能力域 domain_payload 使用明确枚举 allowlist；
18. Analysis Card 含 data_freshness（含条件必填规则和 valid_until 推导参考表）；
19. time_horizon 标准化字段支持 Conflict Detection 机器判断；
20. 增加 `macro_regime_vs_playbook`、`time_horizon_mismatch`、`sentiment_vs_valuation` 冲突规则；
21. Conflict Detection 对 Flag Card 的处理对齐 SPEC-003；
22. 每个能力域输出必须可被 Validation、Conflict Detection、Playbook Evaluation 和 Decision Trace 消费；
23. `value_path` 已明确根节点为 Evidence.`metrics` 字典；
24. `completed + unavailable` 矛盾组合显式禁止；
25. `time_horizon_mismatch` 触发条件精确化为可机器判断的算法；
26. lineage 间接污染局限已显式承认，交付 SPEC-005 + SPEC-009 协同。

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
