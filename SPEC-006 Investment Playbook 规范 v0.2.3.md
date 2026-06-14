# SPEC-006：Investment Playbook 规范

**版本：** v0.2.3
**状态：** Approved
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-004 v0.2.3
**文档类型：** 投资方法规格 / Playbook Schema
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

v0.2.0 在 v0.1.9 基础上关闭残余执行语义缺口。状态由 Review 升级为 Approved。主要补齐：

1. **P0** §17.2 `partial` 触发条件修正——移除不可达的 `multi_rule + all` 场景，聚焦 `multi_label_avoid` 半解析与 `multi_rule + any` 部分 pass/fail；
2. **P1** §26.1/§25：`macro_regime_vs_playbook` 无条件触发 `require_human_review` 为设计意图——宏观域数据缺失本身即信号不确定性，应触发人工复核；
3. **P1** §25 新增 MVP `conflict_type` 枚举表（与 §26.1 `require_review_on` 交叉引用）；
4. **P2** §18.3：Company Event `partial` 域中 derived fact 仍须导出——fact 依赖事件属性而非完整财务数据；
5. **P2** §22.3：`confidence_cap` 下调为绝对值 0.05，下限 0.5；
6. **P2** §9 新增 `priority` 枚举正式声明；
7. **P2** §7.2 第 4 条：`macro_regime_vs_playbook` 检查在 MVP 中通过 Conflict Handling 实现；
8. 小修：§13.2 `none` 拒绝、§29 hash 排除 metadata、§25.1 移除 `need_more_data`。

v0.1.9 在 v0.1.8 基础上关闭执行路径缺口和跨文档接口假设。主要补齐：

1. **P0** §22.3 决策表补充"所有 Hard pass"判断标准（stale_data ≠ pass；
2. **P1** §8.4 补充 `partial` Analysis Card 对 Constraint 可用性的影响声明；
3. **P1** §18.3 声明 derived fact 生产者为 Company Event 能力域（constraint_exports）；
4. **P2** §24.2 补充 Freshness→Hard Constraint 的数据传递机制（stale 标记注入）；
5. **P2** §17.2 补充 `partial` Constraint 触发条件的正向定义；
6. **P2** §26.1 补充 `high_conflict` 判定标准（default_severity = high 触发）；
7. 小修：§45 Q1/Q8 状态标注更新。

v0.1.8 在 v0.1.7 基础上补齐边界场景与字段语义。主要补齐：

1. **P1** §13.3 补充 `any` 所有子规则数据不足时整体升级为 `insufficient_data` + `not_applicable` 通用跳过规则；
2. **P1** §22.3 决策表补充优先级声明（自上而下匹配，满足即停止）；
3. **P1** §14 补充 `multi_label_avoid` 部分解析规则（`all_refs_in_avoid_values` 时保守原则 → `insufficient_data`）；
4. **P1** §11.3 NOTE 扩展：`fact://` boolean threshold 支持（`operator: ==/!=`）；
5. **P2** §25 补充 `default_severity` 字段语义声明（描述性元数据，不影响执行）；
6. **P2** §26.1 补充 `require_review_on` 值来源说明；
7. **P2** §8.4 补充 `domain_status` 来源交叉引用（→ SPEC-004 Analysis Card）；
8. 小修：§46 标题版本号同步。

v0.1.7 在 v0.1.6 基础上关闭残余语义缺口与一致性风险。主要补齐：

1. **P0** §23.2 NOTE 补充 `partial` 时 `on_fail` 不执行（与不计入 fail 计数保持一致）；
2. **P0** §25 NOTE 补充 condition 降级时 block/human_review 类动作的保护性警告；
3. **P0** §33.1 `growth_capex_flag` 子规则跳过时 status = `not_applicable`，整体按剩余子规则计算；
4. **P1** §26.1 补充 `requires_human_review` 多路径触发合并规则（OR 语义）；
5. **P1** §23.2 补充 `passed_with_caution` 的 `confidence_cap` 下调幅度可配置性声明；
6. **P1** §13 补充 `multi_rule` 子规则数据不足时的整体判断规则；
7. **P1** §18.1 补充 `label://`/`fact://` 不可用于 Hard Constraint 的边界声明；
8. **P2** §16 补充 Preference 冲突解决规则（priority → 声明顺序）；
9. **P2** §40 补注：`cashflow_deterioration` 在 `growth_capex_flag = true` 时的 MVP 不执行关系；
10. **P2** §22.3 `overall_result` 决策树显式化（passed → partially_passed → passed_with_caution 边界）；
11. **P2** §11 补充 `ref_vs_threshold` 字符串 threshold 支持说明；
12. 小修：§5.1 JSON 注释说明 §34.2 string ref_vs_threshold 合法 operator 集合。

v0.1.6 在 v0.1.5 基础上关闭执行语义缺口与一致性矛盾。主要补齐：

1. **P0** §23.2 补充 `partial` Constraint 不计入 `passed_with_caution` 触发计数（§23.2 NOTE）；
2. **P0** §25 补充 `condition input_ref` 无法解析时的降级行为（跳过 condition，按无条件形式执行 + Decision Trace NOTE）；
3. **P1** §23.2 补充 `require_human_review` 优先级：当 Soft Constraint fail 中包含 `require_human_review` 时，`overall_result` 优先设为 `requires_human_review`，不聚合为 `passed_with_caution`；
4. **P1** §33.1 FCF 硬约束补充 capital expansion flag 例外说明（§33.1 NOTE）；
5. **P2** §25.2 补充 `operator: "in"` 语义声明 + §10 operator 枚举扩展；
6. **P2** §16 Preference `effect` 字段格式约束补充（MVP 为自由文本 + Decision Trace 展示语义）；
7. **P2** §22.3 补充 `passed_with_caution` 的 `recommended_decision_bounds` 行为说明；
8. **P2** §25.2 示例从 `fundamentals_vs_valuation` 抽象化为通用示例，消除与 §36 的不一致；
9. **P2** §4.4 补充 Playbook 与 Resolved Decision Bounds 合并方向声明；
10. 小修：§41 步骤 3 措辞从 `analysis_incomplete` 修正为 `run_status = analysis_incomplete`。

v0.1.5 在 v0.1.4 基础上修复文档一致性与示范对齐。主要补齐：

1. **P1** §36 `fundamentals_vs_valuation` actions 从 `["block_new_position"]` 改为 `["prefer_wait"]`，与 §23.2 dedup 建议对齐；
2. **P1** `passed_with_caution` 触发逻辑补入 §23.2 聚合规则 + 与 `partially_passed` 的边界说明；
3. **P2** §43 MVP "Preference 记录"更新为区分 `action_ranking` / `confidence_adjustment` 执行方式；
4. **P2** `on_insufficient_data = note` 时 `impact_on_decision` 设为 `neutral`（§42.3 + §19 NOTE）；
5. **P2** `label://valuation_state` 值域来源声明（§25.2 NOTE）；
6. **P2** §45 Q1 暂定 MVP 立场：统一阈值 + 行业适用范围说明（§30.1）；
7. 小修：§5.1 JSON comment 标注、§13.2 `none` MVP 不使用、§24.2 flag 说明、§36 同类型多规则→§45 Q8、§41 步骤 3 早退。

v0.1.4 在 v0.1.3 基础上补齐执行语义边界与缺省声明。主要补齐：

1. **P1** `blocking_conditions` dedup 策略：Hard Constraint 负责 block，Conflict Handling 负责 ranking 时两者不重复记录（§36 + §23.2）；
2. **P1** Soft Constraint `on_insufficient_data` 缺省行为声明（§15）+ §34.2/§34.3/§34.4 补全字段；
3. **P1** §8.4 第 3 条与 Optional Domains `on_missing` 优先级：§8.4 为 Playbook 级阈值，高于单个域设定（§8.4）；
4. **P2** `ref_vs_ref` as_of `flag` 注记与 Constraint `status` 的区分（§12.3）；
5. **P2** `multi_label_avoid` AND 语义显式说明（§14.2）；
6. **P2** `impact_on_decision` 枚举与 `prefer_*` 的关系说明（§19）；
7. **P2** `overall_result` 增加 `passed_with_caution`（§22.3）；
8. **P2** `preference_type = confidence_adjustment` 执行语义（§16）；
9. **P2** 开放问题 Q2/Q4/Q7 暂定立场（§45）；
10. 小修：§5.1 conflict_handling 空对象→占位、§22.1 子字段方向性注释、§29 playbook_source 补枚举、§41 步骤 3.5、§44 补 SPEC-004。

v0.1.3 在 v0.1.2 基础上修复规则引擎实现一致性问题。主要补齐：

1. **P1** `on_hard_constraint_fail` 与 §23.2 分工：`need_more_data`/`stale_data` 从映射中移除，交聚合规则处理（§21.2 + §23.2）；
2. **P1** Conflict Handling 中 `prefer_wait`/`prefer_add_to_watchlist` 执行语义定义：提升 ranking 权重，不移除动作（§25.3 新增）；
3. **P2** `ref_vs_ref` 的 `max_age_days` 取值规则明确化：取两个 ref 各自 Freshness 配置的较小值（§12.3）；
4. **P2** §8.4 第 3 条放宽为 `domain_status ≠ insufficient_data`，补充判断基准（§8.4）；
5. 小修：§34.1 补 `on_insufficient_data`、§36 Conflict Handling 顶层格式说明、§21.2 注释。

v0.1.2 在 v0.1.1 基础上补齐 schema 一致性与执行语义缺口。状态由 Draft 升级为 Review。主要补齐：

1. **P0** `ref_vs_threshold` 顶层/子规则字段名统一（`input_refs` vs `input_ref`）与声明规则（§11.3）；
2. **P0** `multi_label_avoid` 的 `match_policy` 修正为 `all_refs_in_avoid_values` + `avoid_values` 值绑定语义说明（§14）；
3. **P1** `overall_result` 优先级：`fail` > `insufficient_data`/`stale_data`（§23.2）；
4. **P1** `label://event_direction` / `label://event_materiality` → `fact://` 替换（§40、§18.3）；
5. **P2** Soft Constraint `allowed_evidence_types` 缺省规则（§15）；
6. **P2** `ref_vs_ref` 增加跨域 `as_of` 一致性检查（§12.3）；
7. **P2** Invalidating Conditions MVP 执行性质声明（§28）；
8. 小修：§5.2 `risk_tolerance` 归属、§44 补 SPEC-003 依赖、§21.1 `block_add_position` 说明。

v0.1.1 在 v0.1 基础上补齐执行层语义缺口。不改变 Playbook 主体设计。主要补齐：

1. Constraint 的四种 `evaluation_mode` 及对应 schema；
2. `on_missing` / `on_conflict` 枚举收敛与复合语义拆分；
3. `label://event_certainty` 多事件解析规则；
4. Invalidating Conditions 的 `impact` → `trigger_action`；
5. `pe_percentile_5y` freshness 修正；
6. Constraint Evaluation Result 增加 `task_id` / `run_id`；
7. Metadata 与顶层 schema 关系澄清；
8. `risk_tolerance` 字段；
9. `recommended_decision_bounds` 聚合规则重排。

修订后的核心原则是：

```text
Playbook constraints must be executable, not merely descriptive.
```

中文表达：

```text
Playbook 约束必须可执行，而不只是可读。
```

---

## 1. 文档目标

SPEC-006 用于定义 crosslens 中 Investment Playbook 的结构、执行语义、约束类型、输入引用、动作边界、版本管理和默认内置 Playbook。

Investment Playbook 是用户投资方法的结构化表达。

它不是普通投资笔记，也不是提示词模板，而是一个可以被编排器、规则引擎、Playbook Evaluation、Resolved Decision Bounds 和 Decision Trace 使用的可执行投资决策手册。

本 SPEC 重点回答：

1. Investment Playbook 是什么；
2. Playbook 与 Workflow、Capability、Analysis Card、Decision Candidate 的关系是什么；
3. Playbook 如何表达投资风格、周期、资产范围和风险偏好；
4. Hard Constraint、Soft Constraint、Preference、Guardrail Hook 如何定义；
5. Playbook 如何消费 SPEC-004 的 `constraint_exports`；
6. Playbook 如何生成 Playbook Evaluation Report；
7. Playbook 如何影响 Resolved Decision Bounds；
8. Playbook 如何处理数据不足、冲突、过期数据和人工复核；
9. Playbook 如何版本化和进入 Decision Trace；
10. MVP 默认 `capital_cycle_fundamental_playbook` 如何定义。

本 SPEC 不详细定义：

1. 五个分析能力域内部实现；
2. Capability Package 内部封装方式；
3. Metric Registry 完整系统；
4. Guardrail 规则全集；
5. Decision Trace UI；
6. 用户编辑 Playbook 的完整交互界面；
7. 多 Playbook 对比与组合管理。

以上内容由后续 SPEC 定义。

---

## 2. Investment Playbook 的定位

Investment Playbook 是投资判断方法的结构化容器。

它定义：

1. 适用的资产范围；
2. 适用的投资周期；
3. 风险偏好；
4. 必须满足的硬性条件；
5. 需要考虑的软性条件；
6. 行动边界；
7. 数据新鲜度要求；
8. 触发人工复核的条件；
9. 输出建议的表达方式；
10. 结论失效条件。

一句话：

> Investment Playbook turns investment style into executable decision constraints.

中文表达：

> Investment Playbook 把投资风格转化为可执行的决策约束。

---

## 3. Playbook 不是什么

Investment Playbook 不是：

1. 单纯的 Prompt；
2. 长篇投资理念文章；
3. 自动交易策略；
4. 收益预测模型；
5. 选股黑箱；
6. 多 Agent 角色设定；
7. 替用户做最终决策的规则；
8. 无条件适用于所有市场环境的万能模板。

Playbook 只定义"在什么条件下，某种投资方法允许系统给出什么范围内的判断"。

---

## 4. 与其他核心对象的关系

### 4.1 与 Workflow 的关系

Workflow 定义系统执行顺序。
Playbook 定义该顺序中哪些条件必须被检查，以及检查结果如何影响动作边界。

Workflow 回答：系统下一步做什么？
Playbook 回答：用什么投资方法判断？

### 4.2 与 Analysis Card 的关系

Analysis Card 是能力域输出。
Playbook 不直接调用能力域，也不直接生成 Analysis Card。

Playbook 只消费 Analysis Card 中的：

1. `constraint_exports`；
2. `stance`；
3. `confidence`；
4. `data_quality`；
5. `data_freshness`；
6. `supporting_evidence`；
7. `opposing_evidence`；
8. `domain_payload`；
9. `invalidating_conditions`。

### 4.3 与 Playbook Evaluation Report 的关系

Playbook Evaluation Report 是 Playbook 执行后的结果对象。
Playbook 是规则和方法，Playbook Evaluation Report 是本次任务的执行结果。

### 4.4 与 Resolved Decision Bounds 的关系

Playbook Evaluation Report 生成 `recommended_decision_bounds`。
Resolved Decision Bounds 再把 Playbook Evaluation、Validation、Conflict、Guardrail 等约束合并成最终动作边界。
Playbook 不能绕过 Resolved Decision Bounds 直接生成 Decision Candidate。

### 4.5 与 Decision Candidate 的关系

Decision Candidate 的 `suggested_action` 必须满足：

```text
suggested_action ∈ resolved_decision_bounds.allowed_actions
```

Playbook 影响 Decision Candidate，但不直接决定最终建议动作。

> **合并方向声明（v0.1.6）：** Playbook Evaluation Report 生成 `recommended_decision_bounds`，由 Resolved Decision Bounds 进一步合并 Guardrail、Validation 等约束。合并规则中，Guardrail 和 Validation 只能进一步收窄 `allowed_actions`（移除动作或降低 confidence），不得恢复已被 Playbook 移除的动作。完整合并规则由 SPEC-003 和 SPEC-009 定义。

---

## 5. Playbook 顶层 Schema

Playbook 顶层 schema 采用扁平结构（不使用嵌套 `metadata` 对象）。

### 5.1 最小结构

```json
{
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_name": "Capital Cycle Fundamental Playbook",
  "status": "active",
  "playbook_type": "single_stock_investment",
  "risk_tolerance": "medium",
  "created_by": "system",
  "created_at": "2026-06-14T00:00:00Z",
  "updated_at": "2026-06-14T00:00:00Z",
  "description": "面向资本周期与中长期基本面的单股票投资判断手册。",
  "applicability": {},
  "required_domains": [],
  "optional_domains": [],
  "constraints": [],
  "preferences": [],
  "freshness_requirements": [],
  "conflict_handling": {},
  // conflict_handling 实际为以冲突类型为 key 的对象（如 {\"macro_regime_vs_playbook\": {...}}），MVP 最小结构可为 null
  "action_policy": {},
  "human_review_policy": {},
  "output_policy": {},
  "invalidating_conditions": [],
  "versioning": {}
}
```

> **文档 JSON 注释说明（v0.1.7）：** 文档中部分 JSON 示例包含 `//` 格式的行注释或 `_comment` 说明字段。标准 JSON 不支持行注释，这些注释仅供文档阅读，实现时应在解析前移除注释行或替换为 `_comment` 字段（执行时忽略）。

### 5.2 Metadata 类字段说明

> Playbook 顶层 schema 采用扁平结构。§6 的 Playbook Metadata 是对顶层 metadata 类字段（包括 `playbook_id`、`playbook_version`、`playbook_name`、`status`、`playbook_type`、`risk_tolerance` 等）的展开解释，不表示存在一个嵌套的 `metadata` 对象。

---

## 6. Playbook Metadata

### 6.1 字段

```json
{
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_name": "Capital Cycle Fundamental Playbook",
  "status": "active",
  "playbook_type": "single_stock_investment",
  "risk_tolerance": "medium",
  "created_by": "system",
  "created_at": "2026-06-14T00:00:00Z",
  "updated_at": "2026-06-14T00:00:00Z",
  "description": "面向资本周期与中长期基本面的单股票投资判断手册。"
}
```

### 6.2 status 枚举

```text
draft
active
deprecated
archived
```

MVP 阶段默认只使用 `active`。非 `active` 状态（`draft`、`deprecated`、`archived`）的 Playbook 在 MVP 中拒绝执行，规则引擎返回 validation error。开发/测试环境可通过 Run Config 中的 `allow_non_active_playbook = true` 标志绕过此检查（仅限非生产环境），并在 Decision Trace 中标注"非生产状态 Playbook"。

### 6.3 risk_tolerance

> v0.1.1 新增。

```text
low
medium
high
unknown
```

| risk_tolerance | 语义 |
|---|---|
| `low` | 更保守，倾向等待与更高安全边际 |
| `medium` | 默认平衡模式 |
| `high` | 可接受更高波动和更早介入 |
| `unknown` | 未声明风险偏好 |

MVP 默认：`medium`。

---

## 7. Applicability

Applicability 定义 Playbook 适用于什么场景。

### 7.1 Schema

```json
{
  "asset_types": ["stock"],
  "markets": ["US", "HK", "CN"],
  "investment_horizon": {
    "time_horizon_bucket": "medium_term",
    "time_horizon_days_min": 90,
    "time_horizon_days_max": 365
  },
  "supported_task_types": [
    "single_stock_buy_decision",
    "single_stock_hold_review",
    "single_stock_watchlist_review"
  ],
  "preferred_user_profile": [
    "capital_cycle_investor",
    "fundamental_investor",
    "industry_cycle_investor"
  ],
  "not_suitable_for": [
    "intraday_trading",
    "short_term_momentum_trading",
    "pure_sentiment_trading"
  ]
}
```

### 7.2 适用性检查

MVP 阶段，Playbook Applicability 不作为独立 Evaluator。

但系统必须检查：

1. asset_type 是否匹配；
2. task_type 是否匹配；
3. 用户目标周期是否大幅偏离 Playbook 周期；
4. 是否存在显著 `macro_regime_vs_playbook` 风险（MVP 中通过 Conflict Handling §25 实现，非 Invalidating Conditions）；
5. 是否应进入 `requires_human_review`。

完整 Playbook Applicability Evaluator 由后续 SPEC 定义。

---

## 8. Required Domains 与 Optional Domains

### 8.1 Required Domains

Required Domains 是该 Playbook 生成完整 Decision Candidate 的必要能力域。

```json
{
  "required_domains": [
    {
      "domain": "fundamentals",
      "minimum_status": "completed",
      "on_missing": "analysis_incomplete"
    }
  ]
}
```

MVP 默认：`fundamentals` 必须可用。

### 8.2 Optional Domains

Optional Domains 是辅助判断能力域。

```json
{
  "optional_domains": [
    {
      "domain": "macro_meso",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "company_event_catalyst",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "sentiment",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "technical_market",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    }
  ]
}
```

### 8.3 on_missing 枚举

| on_missing | 语义 |
|---|---|
| `analysis_incomplete` | 缺失该域时不能生成完整 Decision Candidate |
| `continue_with_warning` | 可继续，但必须进入 Decision Trace |
| `skip_domain` | 编排器可主动跳过该域 |
| `requires_human_review` | 缺失该域时触发人工复核 |

### 8.4 最小可用能力域规则

SPEC-006 继承 SPEC-003 的最小可用 Analysis Card 阈值。下文中的 `domain_status` 指 Analysis Card 的 `domain_status` 字段（在 SPEC-004 §5 中定义，枚举见 SPEC-004 §5.1），非 SPEC-006 自创概念——此字段由能力域在生成 Analysis Card 时填写，Playbook Evaluation 在步骤 3 消费：

1. 至少 3/5 个能力域返回非 `insufficient_data` 的 Analysis Card；
2. Fundamentals 必须可用；
3. 至少一个非 Fundamentals 能力域 `domain_status ∈ {completed, partial}`。该域无需满足特定 evidence 数量或 confidence 阈值——只要能力域完成或部分完成分析即为有效贡献（背景信息同样可辅助人类判断）。`failed` 或 `skipped` 不计入有效贡献——此约束阻止实现者将能力域执行失败误认为有效参与；
4. 不存在 Block 级 Validation Finding；
5. Playbook 关键 Hard Constraint 可以判断。

> **§8.4 与 `partial` Analysis Card（v0.1.9）：** `domain_status = partial` 的域计入第 3 条"有效贡献"计数。该域导出的 `constraint_exports` 中部分 metric 可能不可用——若 Playbook Constraint 引用了缺失的 metric，对应 Constraint 按 `insufficient_data` 处理，不影响域级别的 `domain_status` 判定。`partial` 域剩余可用 metric 仍可被 Constraint 消费。

> **§8.4 与 Optional Domains `on_missing` 的优先级（v0.1.4）：** §8.4 是 Playbook 级别的最小可用阈值，优先级高于单个 Optional Domain 的 `on_missing` 设定。若四个 Optional Domains 全部返回 `insufficient_data`，即使每个域单独设置了 `on_missing = continue_with_warning`，Playbook 级别仍因违反第 3 条而停止生成完整 Decision Candidate（`analysis_incomplete`）。单个域的 `on_missing` 仅在个别域缺失时生效。

---

## 9. Constraint 类型总览

Playbook 支持三类约束：Hard Constraint、Soft Constraint、Preference。

### 9.1 Hard Constraint

Hard Constraint 是必须由规则引擎执行的硬性条件。MVP 阶段默认只能引用 Computed Evidence metrics。

### 9.2 Soft Constraint

Soft Constraint 可以引用 Computed metrics、Structured facts、labels、Analysis Card stance、domain_payload 和 interpreted findings。必须进入 Decision Trace。

### 9.3 Preference

Preference 表示风格偏好，不应单独阻断动作，但可以影响 action ranking。

### 9.4 `priority` 枚举

> v0.2.0 新增。所有 Constraint 和 Preference 的 `priority` 字段使用以下枚举。

```text
high
medium
low
```

| priority | 语义 | 应用 |
|---|---|---|
| `high` | 优先处理，冲突解决时排前 | 关键 Hard/Soft Constraint、核心 Preference |
| `medium` | 默认 | 一般 Soft Constraint |
| `low` | 辅助判断 | 次要 Preference、轻度提示 |

---

## 10. Constraint Evaluation Mode

> v0.1.1 新增。每个 Constraint 必须声明 `evaluation_mode`。

### 10.1 evaluation_mode 枚举

```text
ref_vs_threshold
ref_vs_ref
multi_rule
multi_label_avoid
```

### 10.2 模式说明

| evaluation_mode | 含义 | 适用场景 |
|---|---|---|
| `ref_vs_threshold` | 一个 input_ref 与固定 threshold 比较 | PE 分位 <= 0.8 |
| `ref_vs_ref` | 两个 ref 相互比较 | 收入增速 >= 行业中位数 |
| `multi_rule` | 多条子规则组合判断 | 毛利率变化 + FCF 同时满足 |
| `multi_label_avoid` | 多个 label 不应同时落入 avoid_values | 利率收紧 + 流动性收缩 |

规则引擎不得在缺少 `evaluation_mode` 的情况下推断 Constraint 类型。

---

## 11. ref_vs_threshold 模式

### 11.1 Schema

```json
{
  "constraint_id": "valuation_margin_001",
  "name": "估值不过度昂贵",
  "constraint_type": "hard",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["metric://pe_percentile_5y"],
  "operator": "<=",
  "threshold": 0.8,
  "description": "估值分位不得过高，否则禁止新开仓。",
  "priority": "high",
  "on_pass": "support",
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "evidence_requirements": {
    "required_determinism_level": "computed",
    "allow_structured_evidence": false,
    "allow_interpreted_evidence": false
  },
  "freshness_requirement": {
    "freshness_level": "quarterly",
    "max_age_days": 120
  }
}
```

### 11.2 执行语义

```text
value(input_refs[0]) <= threshold
```

### 11.3 约束

1. `input_refs` 必须恰好包含 1 个元素；
2. 必须包含 `operator`；
3. 必须包含 `threshold`；
4. `threshold` 必须与 input_ref 的 value_type 可比较。

> **字符串 threshold 支持（v0.1.7）：** `ref_vs_threshold` 的 `threshold` 支持数值和字符串两种类型。字符串 threshold 的合法 `operator` 为 `==` 和 `!=`。当 input_ref 引用 `label://` 类型时，`operator = "!="` 配合字符串 threshold 用于判断标签值不等于指定枚举值（如 `label://sentiment_state != "overheated"`）。此支持仅适用于 Soft Constraint。

> **boolean threshold 支持（v0.1.8）：** `ref_vs_threshold` 的 `threshold` 同时支持 boolean 类型（`true`/`false`），合法 `operator` 同为 `==` 和 `!=`。当 input_ref 引用 `fact://` 类型且值为 boolean 时（如 `fact://any_material_event_low_certainty != true`，见 §34.4），规则引擎按布尔相等性判断。此支持仅适用于 Soft Constraint。

> **字段名规则（v0.1.2）：** 顶层 `ref_vs_threshold` Constraint 使用 `input_refs`（数组）。`multi_rule` 内的子规则使用 `input_ref`（单数字符串，因子规则已预设单值语义）。规则引擎解析 `ref_vs_threshold` 时：若在顶层 Constraint 上下文中，读取 `input_refs[0]`；若在 `multi_rule` 子规则上下文中，读取 `input_ref`。文档校验器应在 Schema Validation 阶段检查字段名一致性。

---

## 12. ref_vs_ref 模式

> v0.1.1 新增。

### 12.1 Schema

```json
{
  "constraint_id": "growth_vs_industry_001",
  "name": "收入增长不弱于行业",
  "constraint_type": "hard",
  "evaluation_mode": "ref_vs_ref",
  "left_ref": "metric://revenue_growth_ttm",
  "right_ref": "metric://industry_median_revenue_growth_ttm",
  "operator": ">=",
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "as_of_mismatch_policy": "note"
}
```

### 12.2 执行语义

```text
value(left_ref) >= value(right_ref)
```

### 12.3 约束

1. 必须包含 `left_ref`；
2. 必须包含 `right_ref`；
3. 必须包含 `operator`；
4. 不应包含 `threshold`；
5. `left_ref` 与 `right_ref` 的 value_type 必须兼容；
6. 任一 ref 无法解析，Constraint status = `insufficient_data`；
7. 任一 ref 数据过期，Constraint status = `stale_data`；
8. `left_ref` 与 `right_ref` 的 `data_freshness.as_of` 差值应不超过约束基准值。基准值取两个 ref 各自在 Freshness Requirements 中定义的最大 `max_age_days` 的较小值。若任一 ref 未在 Freshness Requirements 中定义，取 Playbook 级默认值（如有）；若均无，跳过该检查并标记 NOTE。若超过，按 `as_of_mismatch_policy` 处理。`as_of_mismatch_policy` 由 Playbook 或 Run Config 配置，枚举为 `note | stale_data | require_human_review`，MVP 默认 `note`（进入 Decision Trace 注记但不改变 Constraint status）。`stale_data` 选项会将 Constraint status 设为 `stale_data`（仅建议用于 Hard Constraint）；`require_human_review` 会将该 Constraint 的 `on_fail` 覆盖为 `require_human_review`。

---

## 13. multi_rule 模式

> v0.1.1 新增。

### 13.1 Schema

```json
{
  "constraint_id": "fundamental_quality_001",
  "name": "财务质量未恶化",
  "constraint_type": "hard",
  "evaluation_mode": "multi_rule",
  "condition_logic": "all",
  "rules": [
    {
      "rule_id": "gross_margin_not_deteriorating",
      "evaluation_mode": "ref_vs_threshold",
      "input_ref": "metric://gross_margin_qoq_change",
      "operator": ">=",
      "threshold": -0.05
    },
    {
      "rule_id": "fcf_margin_positive",
      "evaluation_mode": "ref_vs_threshold",
      "input_ref": "metric://fcf_margin_ttm",
      "operator": ">",
      "threshold": 0
    }
  ],
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "as_of_mismatch_policy": "note"
}
```

说明：允许毛利率小幅波动（下降不超过 5 百分点），且自由现金流率必须为正。

### 13.2 condition_logic 枚举

```text
all
any
none
```

| condition_logic | 语义 |
|---|---|
| `all` | 所有子规则通过，Constraint 才通过 |
| `any` | 任一子规则通过，Constraint 即通过 |
| `none` | 所有子规则均不通过，Constraint 才通过（MVP 暂不使用此值。MVP 规则引擎应在 Schema Validation 阶段拒绝 `condition_logic = none` 的 Constraint，返回 validation error） |

### 13.3 子规则数据不足时的整体判断

> v0.1.7 新增。

当 `multi_rule` 中的子规则存在 `insufficient_data` 或 `stale_data` 时，整体 Constraint status 按以下规则确定：

| 子规则状态 | condition_logic = all | condition_logic = any | condition_logic = none |
|---|---|---|---|
| 任一子规则 `insufficient_data` 或 `stale_data` | 整体为 `insufficient_data` | 跳过该子规则，按剩余子规则计算 | 整体为 `insufficient_data` |

若顶层 Constraint 的 `on_insufficient_data` 未定义，默认继承子规则的 `status`。子规则自身无 `on_insufficient_data`/`on_stale_data` 字段——所有数据不足/过期情况由顶层统一处理。

**`any` 全部数据不足（v0.1.8）：** 若 `condition_logic = any` 下所有子规则均为 `insufficient_data` 或 `stale_data`（跳过后剩余子规则为空集），整体 Constraint status 升级为 `insufficient_data`，不返回 `pass` 或 `fail`。

**`not_applicable` 子规则处理（v0.1.8）：** 子规则 status = `not_applicable`（如 §33.1 `growth_capex_flag` 触发的例外）时，无论 `condition_logic` 如何，均跳过该子规则按剩余子规则计算。此规则与 `any` 模式下 `insufficient_data` 的跳过逻辑平行。

---

## 14. multi_label_avoid 模式

> v0.1.1 新增。

### 14.1 Schema

```json
{
  "constraint_id": "macro_environment_001",
  "name": "宏观环境不明显逆风",
  "constraint_type": "soft",
  "evaluation_mode": "multi_label_avoid",
  "input_refs": [
    "label://rate_environment",
    "label://liquidity_environment"
  ],
  "avoid_values": ["tightening", "contracting"],
  "match_policy": "all_refs_in_avoid_values",
  "on_fail": "require_human_review",
  "on_insufficient_data": "note"
}
```

### 14.2 match_policy 枚举

```text
any_avoid_value_present
all_avoid_values_present
all_refs_in_avoid_values
```

| match_policy | 触发 fail 的条件 |
|---|---|
| `any_avoid_value_present` | 任一 input_ref 的值落入 avoid_values |
| `all_avoid_values_present` | avoid_values 中所有值都至少出现一次 |
| `all_refs_in_avoid_values` | 所有 input_refs 的值都落入 avoid_values |

MVP 至少实现 `all_refs_in_avoid_values`。

> **`avoid_values` 值绑定语义（v0.1.2）：** `avoid_values` 不与 `input_refs` 逐一绑定。匹配基于整体值集合——即"所有 input_ref 的值是否都落在 avoid_values 集合中"。例如 `rate_environment = "tightening"` + `liquidity_environment = "contracting"` → 两个值都 ∈ `["tightening", "contracting"]` → 触发。若需要精确绑定（如"rate_environment 必须是 tightening 且 liquidity_environment 必须是 contracting"），应使用 `multi_rule` + 两个独立 `ref_vs_threshold` 子规则。

> **`all_refs_in_avoid_values` 为 AND 语义（v0.1.4）：** 所有 input_ref 的值都必须落入 avoid_values 集合才触发。若部分 ref 在 avoid_values 中、部分不在（如三个 ref 仅两个匹配），不触发 fail。若需要 OR 语义（任一 ref 落入 avoid_values 即触发），使用 `any_avoid_value_present`。若需要精确值绑定（指定哪个 ref 取哪个值），使用 `multi_rule`。

> **部分解析规则（v0.1.8）：** `match_policy = all_refs_in_avoid_values` 或 `all_avoid_values_present` 时，若部分 `input_ref` 无法解析，整体 status = `insufficient_data`（保守原则）。若已解析的 ref 值已可确定不触发 fail（如任一已解析 ref 不在 avoid_values 中），可按 `pass` 处理并标注 Decision Trace NOTE，但 MVP 不强制要求此优化分支。

---

## 15. Soft Constraint 规则

Soft Constraint 可以引用 metric、fact、label、stance、domain_payload、interpreted finding。

### 15.1 Schema

```json
{
  "constraint_id": "sentiment_overheat_001",
  "name": "市场情绪不过热",
  "constraint_type": "soft",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["label://sentiment_state"],
  "operator": "!=",
  "threshold": "overheated",
  "priority": "medium",
  "on_pass": "neutral",
  "on_fail": "lower_confidence",
  "on_insufficient_data": "note",
  "allowed_evidence_types": ["structured", "computed"]
}
```

>`allowed_evidence_types` 为可选字段。缺省时 Soft Constraint 允许引用所有 evidence type（computed、structured、interpreted），但 Interpreted Evidence 不得单独支撑强建议（§20.3）。

### 15.2 Soft Constraint 不得直接产生强建议

Soft Constraint 可以：降低 confidence、添加 caution、移除强动作、要求人工复核、进入 Decision Trace。
不得单独生成 `buy`、`strong_buy`、`strong_sell`。

### 15.3 `on_insufficient_data` 缺省行为

> v0.1.4 新增。

`on_insufficient_data` 为 Soft Constraint 的可选字段。**缺省值为 `note`**（进入 Decision Trace 但不改变动作边界）。若 Playbook 需要更强的响应（如 `require_human_review`），必须显式声明。

---

## 16. Preference Schema

```json
{
  "preference_id": "prefer_margin_of_safety",
  "name": "偏好安全边际",
  "description": "估值没有安全边际时，即使基本面较强，也倾向等待。",
  "preference_type": "action_ranking",
  "priority": "high",
  "effect": "prefer_wait_over_buy_when_valuation_expensive"
}
```

Preference 可以影响 action ranking、action_selection_reason、Decision Trace 表达、confidence explanation。不得绕过 Hard Constraint 或 Guardrail。

### 16.1 `preference_type` 枚举与执行语义

> v0.1.4 新增。

```text
action_ranking
confidence_adjustment
```

| preference_type | 语义 | MVP 执行方式 | MVP 是否实际执行 |
|---|---|---|---|
| `action_ranking` | 影响建议动作排序 | 由实现层定义排序权重；步骤 9 应用 | ✅ 是 |
| `confidence_adjustment` | 降低框架层面的置信度 | MVP 阶段仅作为 Decision Trace 说明，不自动修改 confidence cap。若需要自动修改 cap，由 SPEC-009 Evaluator 后续统一定义 | ❌ 否（仅记录，不执行） |

> **`effect` 字段格式（v0.1.6）：** Preference 的 `effect` 字段在 MVP 阶段为自由文本字符串（如 `prefer_wait_over_buy_when_valuation_expensive`）。规则引擎不直接解析该文本——实际排序逻辑由实现层按 `preference_type` 分类硬编码，`effect` 文本仅用于 Decision Trace 展示和人类阅读。

> **Preference 冲突解决（v0.1.7）：** 多个 Preference 同时触发时，按 `priority` 字段（`high` > `medium` > `low`）排序；相同 priority 时按 Playbook 中的声明顺序。优先级更高的 Preference 在 `action_selection_reason` 中排在前面。冲突的 Preference 不互相覆盖，均被记录但排序靠前的更显著。

---

## 17. Constraint Evaluation Result

### 17.1 Schema

```json
{
  "constraint_evaluation_result_id": "cer_001",
  "task_id": "task_001",
  "run_id": "run_001",
  "constraint_id": "valuation_margin_001",
  "constraint_type": "hard",
  "evaluation_mode": "ref_vs_threshold",
  "status": "fail",
  "input_resolution": [
    {
      "input_ref": "metric://pe_percentile_5y",
      "export_ref": "metric://pe_percentile_5y",
      "evidence_ref": "ev_valuation_001",
      "value": 0.83,
      "determinism_level": "computed",
      "data_quality": "high",
      "freshness_level": "quarterly"
    }
  ],
  "operator": "<=",
  "threshold": 0.8,
  "result_value": false,
  "impact_on_decision": "block_new_position",
  "reason": "PE 估值分位高于 Playbook 允许阈值。"
}
```

### 17.2 status 枚举

```text
pass
fail
partial
insufficient_data
stale_data
not_applicable
error
```

`partial` 触发条件（v0.2.3 修正）：Constraint 条件部分满足但不足以判定整体通过或失败。实际触发场景为：(1) `multi_label_avoid` 中部分 `input_ref` 无法解析但已解析 ref 已可判定不触发 fail；(2) `multi_rule + condition_logic = any` 时无子规则明确 pass，存在 `fail` 与 `insufficient_data` 混合，且排除 `insufficient_data` 后剩余子规则无法确定倾向方向。`multi_rule + any` 的判定规则为：若任一子规则 pass → 整体 pass；若全部 insufficient_data/stale_data → 整体 insufficient_data；若有 fail 但无 pass → 整体 fail；若有 fail 与 insufficient_data 混合但无 pass，且剩余可判定子规则（排除 insufficient_data）全部为 fail → 整体 fail；若有 fail 与 insufficient_data 混合但无 pass，且剩余可判定子规则 mixed → 整体 partial。完整规则见 §13.3。

---

## 18. input_refs 解析规则

### 18.1 引用格式

MVP 阶段支持：`metric://{metric_id}`、`fact://{fact_id}`、`label://{label_id}`。

> **Hard Constraint 引用限制（v0.1.7）：** Hard Constraint 的 `input_refs` 仅允许 `metric://` 格式。`fact://` 和 `label://` 仅可用于 Soft Constraint 和 Conflict Handling `condition` 字段。此规则与 §20.1 Hard Constraint 输入限制一致（仅允许 Computed Evidence）。

### 18.2 解析要求

规则引擎执行 Constraint 前，必须解析每个 input_ref，并获得：export_ref、export_type、evidence_ref、value 或 label_value、determinism_level、can_support_hard_constraint、allowed_constraint_types、data_quality、data_freshness、confidence（若适用）。

如果无法解析，Constraint status = `insufficient_data`。

### 18.3 label://event_certainty 多事件解析规则

> v0.1.1 新增。

Company Event / Catalyst 的 `event_certainty` 是 `event_list[]` 内每个事件的属性，不是全局单值。

当 Playbook 引用事件级 label 时，默认解析当前任务相关事件集合中的代表事件：

1. 优先选择 `event_materiality = high` 的事件；
2. 若多个事件同为 high，选择离当前任务时间最近的事件；
3. 若仍无法唯一确定，选择 `event_direction = negative` 的事件；
4. 若仍无法唯一确定，返回 `ambiguous_label_ref`；
5. `ambiguous_label_ref` 应导致该 Soft Constraint 或 Conflict Handling 引用直接触发 `requires_human_review`。**此路径独立于 `on_fail`——即使在 §23.2 NOTE 中 `status = partial` 的 Constraint 不执行 `on_fail`，`ambiguous_label_ref` 在解析阶段（步骤 4）即触发人工复核标记**，不依赖 Constraint 评估结果传播。触发后规则引擎应继续执行剩余步骤（步骤 5-12），不短路退出，以确保 Decision Trace 完整，同时在最终 Playbook Evaluation Report 中合并 `requires_human_review = true`。

MVP 推荐使用 derived fact 避免歧义：

```
fact://any_material_event_low_certainty
fact://latest_material_event_is_confirmed
fact://any_material_negative_event_unresolved
```

> **derived fact 生产者（v0.1.9）：** 上述 derived fact（`any_material_event_*`）由 **Company Event / Catalyst 能力域**在生成 Analysis Card 时作为 `constraint_exports` 的一部分导出（引用格式 `fact://`）。Playbook 不负责派生 fact——能力域基于 `event_list` 内的原始事件属性生成 derived fact 并注入 Analysis Card。即使能力域 `domain_status = partial`（如部分事件数据不可用），只要 `event_list` 非空，derived fact 仍须导出——fact 依赖事件存在性和属性标签，非完整财务数据。若 `event_list` 为空，fact 不导出。

---

## 19. impact_on_decision

Playbook Constraint 使用 SPEC-003 的 `impact_on_decision` 枚举。

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

| impact_on_decision | 语义 |
|---|---|
| support | 支持当前 Playbook 判断 |
| neutral | 中性 |
| caution | 增加谨慎说明 |
| lower_confidence | 降低置信度上限 |
| block_strong_buy | 禁止强买入 |
| block_strong_sell | 禁止强卖出 |
| block_new_position | 禁止新开仓 |
| block_add_position | 禁止加仓（MVP 中 `add_position` 为默认不支持动作，此值用于未来扩展） |
| require_human_review | 要求人工复核 |
| need_more_data | 数据不足，要求补充数据 |

> **`note` 语义（v0.1.5）：** `note` 不是 `impact_on_decision` 枚举值——它表示"进入 Decision Trace 记录注记，但不影响 `allowed_actions`"。当 Constraint 的 `on_insufficient_data = note` 时，`impact_on_decision` 应设为 `neutral`（同 §42.3）。

> **`prefer_*` 与 `impact_on_decision` 的关系（v0.1.4）：** `prefer_wait`、`prefer_add_to_watchlist` 等 ranking 类动作不属于 `impact_on_decision` 枚举。它们不修改 `allowed_actions` 集合，仅影响动作排序和 `action_selection_reason`。完整语义见 §25.4。

---

## 20. Hard Constraint 规则

### 20.1 输入限制

Hard Constraint 默认只能引用 `export_type = metric`、`determinism_level = computed`、`can_support_hard_constraint = true`、`allowed_constraint_types` 含 `hard` 的 export。若 `can_support_hard_constraint` 属性缺失，默认值为 `false`（保守原则——未显式声明支撑能力的 metric 不得进入 Hard Constraint 判定）。

### 20.2 Structured Evidence

Structured Evidence 默认不得直接支撑 Hard Constraint。若未来需要 conditional hard constraint，必须由 SPEC-006 Playbook 或 SPEC-009 Governance 显式声明，且该 export 仍不得设置 `can_support_hard_constraint = true`。

### 20.3 Interpreted Evidence

Interpreted Evidence 不得作为 Hard Constraint 的唯一输入。若引用，Constraint 必须降级为 Soft Constraint 或触发 Validation Flag。

### 20.4 确定性污染

继承 SPEC-003：

```text
A deterministic rule over uncertain evidence is not fully deterministic.
```

---

## 21. Action Policy

### 21.1 默认动作集合

MVP 动作集合继承 SPEC-003：

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

MVP 默认不支持 `strong_buy`、`strong_sell`、`add_position`。

### 21.2 Schema

```json
{
  "default_allowed_actions": [
    "buy", "hold", "wait", "avoid", "reduce",
    "add_to_watchlist", "hold_if_already_owned", "need_more_data"
  ],
  "default_blocked_actions": ["strong_buy", "strong_sell", "add_position"],
  "on_hard_constraint_fail": {
    "block_new_position": ["buy"],
    "block_add_position": ["add_position"]
  }
}
```

> **`on_hard_constraint_fail` 分工（v0.1.3）：** 此映射仅处理 `block_*` 类的动作移除逻辑。`need_more_data` 和 `stale_data` 的处理由 §23.2 聚合规则负责（设置 `overall_result` 而非直接移除动作）。因此 `on_hard_constraint_fail` 中不应包含 `need_more_data` 或 `stale_data` 作为 key。

---

## 22. Playbook Evaluation Report

### 22.1 Schema

```json
{
  "playbook_evaluation_report_id": "pbe_001",
  "task_id": "task_001",
  "run_id": "run_001",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_snapshot_hash": "sha256:...",
  "applicability_status": "applicable",
  "constraint_results": [],
  "preference_results": [],
  "blocking_conditions": [],
  "cautionary_conditions": [],
  "overall_result": "not_passed_for_new_buy",
  "recommended_decision_bounds": [
    "wait",
    "add_to_watchlist",
    "hold_if_already_owned"
  ],
  "requires_human_review": false,
  "confidence_cap_adjustments": [],
  "reasoning": []
  // confidence_cap_adjustments 元素格式与 reasoning 元素格式由 SPEC-008 Decision Trace 定义
}
```

### 22.2 applicability_status 枚举

```text
applicable
partially_applicable
not_applicable
requires_human_review
unknown
```

### 22.3 overall_result 枚举

```text
passed
passed_with_caution
partially_passed
not_passed_for_new_buy
not_passed_for_add_position
not_suitable_for_playbook
need_more_data
requires_human_review
```

| overall_result | 语义 |
|---|---|
| `passed` | 所有 Hard Constraint 通过，Soft Constraint 无显著 fail |
| `passed_with_caution` | 所有 Hard Constraint 通过，但 ≥2 个 Soft Constraint fail。`recommended_decision_bounds` 同 `passed`，`confidence_cap` 下调 0.05 |
| `partially_passed` | 部分通过，但尚不足以阻断 Decision Candidate |
| `not_passed_for_new_buy` | Hard Constraint 明确禁止新开仓 |
| `not_passed_for_add_position` | Hard Constraint 禁止加仓 |
| `not_suitable_for_playbook` | 当前资产或环境不适用此 Playbook |
| `need_more_data` | 关键数据缺失或过期 |
| `requires_human_review` | 触发人工复核条件 |

> **`overall_result` 决策树（v0.1.7）：** 决策树在 §8.4 最小可用能力域规则通过后执行。若 §8.4 触发 `analysis_incomplete`，不进入决策树。以下条件按优先级从高到低匹配，第一个满足即停止。以下条件中"所有 Hard pass"的判断标准为：所有 Hard Constraint 的 `status ∈ {pass, not_applicable}`。`stale_data`、`insufficient_data`、`partial` 不视为 `pass`。**若所有 Hard Constraint 均为 `not_applicable` 且无一条实际 `pass`，视为"所有 Hard pass"（全部跳过等价于无阻碍），走相应 Soft fail 判定分支。**

| 条件 | overall_result |
|---|---|
| 任一 Soft Constraint fail 含 `require_human_review`（优先） | `requires_human_review` |
| 任一 Hard Constraint fail（`block_new_position`） | `not_passed_for_new_buy` |
| 所有 Hard pass，Soft fail = 0 | `passed` |
| 所有 Hard pass，0 < Soft fail < 2 | `partially_passed` |
| 所有 Hard pass，Soft fail ≥ 2 | `passed_with_caution` |
| 任一 Hard Constraint `insufficient_data` 或 `stale_data` | `need_more_data` |

---

## 23. recommended_decision_bounds 聚合规则

> v0.1.1 重排：合并原 §19.1 与 §19.2 为有序执行列表。

### 23.1 执行顺序

Playbook Evaluation 按以下顺序执行：

1. 从 Action Policy 的 `default_allowed_actions` 开始；
2. 移除 Action Policy 的 `default_blocked_actions`；
3. 检查 Required Domains；
4. 解析所有 Constraint input_refs；
5. 检查 data freshness；
6. 执行 Hard Constraints；
7. 执行 Soft Constraints；
8. 应用 Conflict Handling Policy；
9. 应用 Preferences；
10. 生成 `recommended_decision_bounds`；
11. 记录所有被移除动作及原因；
12. 生成 Playbook Evaluation Report。

### 23.2 聚合规则

在步骤 6-9 中应用以下规则：

1. 任一关键 Hard Constraint `fail` 且 impact 为 `block_new_position` → 移除 `buy`；
2. 任一关键 Hard Constraint `insufficient_data` 且 `on_insufficient_data = need_more_data` → `overall_result = need_more_data`；
3. 任一 Hard Constraint `stale_data` 且 `on_stale_data = need_more_data` → `overall_result = need_more_data`；
4. 多个 Soft Constraint fail → 降低 confidence cap。此规则仅在 Soft fail ≥ 2 时触发（与规则 5 同步）；Soft fail = 1 仅触发 `partially_passed` 状态，不降低 confidence cap；
5. 所有 Hard Constraint 通过但 Soft Constraint fail ≥ 2 → `overall_result = passed_with_caution`（v0.1.5 新增）；
6. Conflict Handling 可移除动作或降低 confidence；
7. Preference 只影响动作排序，不得恢复被移除动作；
8. Guardrail 与 Validation 仍可在 Resolved Decision Bounds 阶段覆盖 Playbook 结果；
9. 所有 Hard Constraint `status = not_applicable` 且无一实际 `pass`，视同所有 Hard pass，继续执行 Soft Constraint 判定（v0.2.3 新增）。

> **`passed_with_caution` 与 `partially_passed` 的边界（v0.1.5，v0.1.6 修正）：** `passed_with_caution` = 所有 Hard Constraint 通过 + Soft Constraint fail ≥ 2。`partially_passed` = 无 Hard Constraint fail 但 Soft Constraint fail < 2。两者均为非阻断状态，区别在于 Decision Trace 展示的醒目程度和 `confidence_cap` 的下调幅度。MVP 暂定 Soft Constraint fail 阈值为 2，可由 Run Config 配置。

> **`partial` 状态 Constraint 处理（v0.1.6）：** `status = partial` 的 Constraint 不计入 Soft Constraint `fail` 计数，且 `on_fail` 不执行。此状态仅进入 Decision Trace 注记。仅 `status = fail` 的 Constraint 计入 Soft Constraint fail 计数且执行 `on_fail`。

> **`require_human_review` 优先级（v0.1.6）：** 若任何 Soft Constraint 的 `on_fail` 包含 `require_human_review` 且该 Constraint 实际 fail，`overall_result` 优先设为 `requires_human_review`。此值不参与 `passed_with_caution` 聚合——即使剩余 Soft Constraint fail < 2。

> **`confidence_cap` 下调幅度（v0.1.7）：** `passed_with_caution` 的 `confidence_cap` 默认绝对值下调 0.05，与 Soft Constraint fail 阈值（2）一样，可由 Run Config 配置。下调后 confidence_cap 下限为 0.5——若基础 cap 低于或接近 0.5，下调至不低于 0.5。

> **`blocking_conditions` dedup 策略（v0.1.4）：** 若同一禁止条件由 Hard Constraint `on_fail` 和 Conflict Handling `actions` 双重触发，`blocking_conditions` 列表应去重——同一条 `block_new_position` 只记录一次，来源标注为 `[constraint_id, conflict_type]`。默认 Playbook 已按设计建议修正：Hard Constraint（`valuation_margin_001`）负责 block，Conflict Handling（`fundamentals_vs_valuation`）使用 `prefer_wait` 负责 ranking。

> **`overall_result` 优先级（v0.1.2）：** 规则 1（`fail`）优先于规则 2/3（`insufficient_data`/`stale_data`）。若同时存在 Hard Constraint `fail`，`overall_result` 应保持 `not_passed_for_new_buy`，不因数据缺口覆盖为 `need_more_data`。数据缺口仍须通过 Decision Trace 标记，但不应改变 `fail` 已确立的动作禁止信号。

---

## 24. Freshness Requirements

### 24.1 Schema

```json
{
  "freshness_requirements": [
    {
      "input_ref": "metric://revenue_growth_ttm",
      "freshness_level": "quarterly",
      "max_age_days": 120,
      "on_stale_data": "need_more_data"
    },
    {
      "input_ref": "metric://rsi_14d",
      "freshness_level": "daily",
      "max_age_days": 3,
      "on_stale_data": "flag"
    }
  ]
}
```

### 24.2 规则

1. Hard Constraint 引用的数据必须满足 freshness requirement；
2. 若关键 Hard Constraint 数据过期，应返回 `stale_data`；
3. `stale_data` 必须进入 Decision Trace；
4. 对于 Fundamentals，季度数据过期通常触发 `need_more_data`；
5. 对于 Technical / Market，日频数据过期通常触发 `flag` 或 `need_more_data`。此处 `flag` 为 Decision Trace 注记，不修改 Constraint `status`（同 §12.3）。

> **Freshness→Hard Constraint 数据传递（v0.1.9）：** Freshness 检查（§23.1 步骤 5）的结果以 `data_freshness_status` 注记附加在对应 input_ref 的解析结果中。步骤 6 执行 Hard Constraint 时，若发现 input_ref 携带 `stale` 标记，直接将 Constraint `status` 设为 `stale_data`，不执行 operator/threshold 比较逻辑。Constellation 中仍保留 input_ref 的已解析 value（如有），以便 Decision Trace 记录。

---

## 25. Conflict Handling

> v0.1.1 收紧：`on_conflict` 拆分为可执行 `actions` 数组 + 可选 `condition`。

### 25.1 MVP conflict_type 枚举

> v0.2.0 新增。与 §26.1 `require_review_on` 列表交叉引用。

```text
macro_regime_vs_playbook
fundamentals_vs_valuation
sentiment_vs_valuation
technical_vs_fundamentals
time_horizon_mismatch
```

以上五个为 MVP 支持的冲突类型。§26.1 `require_review_on` 中的 `macro_regime_vs_playbook` 引用此表中的值。新增类型需同时更新两处。若编排器产生某冲突类型但 Playbook 中无对应 Conflict Handling 规则，默认按 `note` 处理并进入 Decision Trace（兜底行为）。

### 25.2 on_conflict 可执行枚举

```text
note
lower_confidence
block_new_position
block_add_position
require_human_review
prefer_wait
prefer_add_to_watchlist
```

>`block_add_position` 用于未来扩展。MVP 中 `add_position` 为默认不支持动作。

>`need_more_data` 不在此枚举中——该值由 §23.2 聚合规则在 Hard Constraint 数据不足/过期时设置 `overall_result`，非 Conflict Handling 层产生。

### 25.3 Schema

带条件的 Conflict Handling（通用示例，演示 `condition` + `operator: "in"` 格式）：

```json
{
  "conflict_type": "sentiment_vs_valuation",
  "default_severity": "high",
  "condition": {
    "input_ref": "label://sentiment_state",
    "operator": "in",
    "values": ["overheated", "bullish"]
  },
  "actions": ["prefer_wait"]
}
```

> **`operator: "in"` 语义（v0.1.6）：** `"in"` 表示集合成员判断——`input_ref 的值 ∈ values 集合`。支持 `"in"` 和 `"not_in"` 两种 variant，仅限 Conflict Handling `condition` 字段使用。与 Constraint 的 `operator`（`<=`、`>=`、`!=` 等数值比较算子）分属不同上下文。

无条件的 Conflict Handling：

```json
{
  "conflict_type": "macro_regime_vs_playbook",
  "default_severity": "high",
  "actions": ["require_human_review"]
}
```

> **`label://valuation_state` 值域来源（v0.1.5）：** Conflict Handling condition 中引用的 label 值（如 `"expensive"`、`"very_expensive"`）的值域由 SPEC-004 能力域的 `constraint_exports` 声明。Playbook 引用的 label 值必须是该声明中的合法值（见 SPEC-004 §19.1 `valuation_state` 枚举）。MVP 阶段由实现层保证一致性；完整 label registry 由 SPEC-004/SPEC-005 定义。

> **Schema Validation 阶段检查（v0.2.2）：** Playbook 加载时，规则引擎应对 Conflict Handling `condition` 中的 `values` 列表与已注册的 label 值域做一致性校验。若 `values` 中的值与注册值域不匹配，返回 **validation warning**（MVP 不阻断加载，但必须记录并提示）。此检查防止 SPEC-004 枚举变更后 Playbook 中 condition 静默降级为无条件触发。

> **`condition input_ref` 降级（v0.1.6，v0.2.3 显式化执行顺序）：** 执行顺序为：(1) 优先尝试从其他可解析 ref 推断 condition 结果；(2) 若无法推断，按无条件形式（全量触发 `actions`）执行；(3) 两种情况均须在 Decision Trace 中标注原因。若 `actions` 包含 `require_human_review` 或 `block_*` 类动作，降级时 Decision Trace 中须显式标注"因 condition 输入缺失而全量触发阻断动作"。

### 25.4 prefer_wait / prefer_add_to_watchlist 执行语义

> v0.1.3 新增。

Conflict Handling 的 `prefer_wait` 和 `prefer_add_to_watchlist` 与 §16 Preference 的 `action_ranking` 类型共享执行逻辑：**提升对应动作的 ranking 权重，但不移除其他动作，不改变 `allowed_actions` 集合**。

两者的区别在于触发层：

| 来源 | 触发步骤 | 语义 |
|---|---|---|
| Conflict Handling `prefer_wait` | 步骤 8 | 跨域冲突存在时，偏好等待 |
| Preference `prefer_wait_over_buy_when_valuation_expensive` | 步骤 9 | 风格偏好，估值缺乏安全边际时偏好等待 |

两者可以叠加：若 Conflict Handling 和 Preference 都偏好 `wait`，Decision Candidate 的 `action_selection_reason` 应记录双重原因。

> **`default_severity` 字段语义（v0.1.8）：** `default_severity`（`high`/`medium`/`low`）为描述性元数据，不影响 `actions` 的执行逻辑或触发方式。仅用于 Decision Trace 展示和人类判断优先级参考。若未来需要基于 severity 的执行行为，由 SPEC-007 Orchestration 定义。

---

## 26. Human Review Policy

### 26.1 Schema

```json
{
  "human_review_policy": {
    "require_review_on": [
      "high_conflict",
      "guardrail_block",
      "validation_block",
      "macro_regime_vs_playbook",
      "hard_constraint_insufficient_data",
      "major_company_event_with_low_certainty"
    ],
    "allow_decision_candidate_before_review": false
  }
}
```

若触发，Playbook Evaluation Report 标记 `requires_human_review = true`。

> **多路径合并规则（v0.1.7）：** `requires_human_review` 可以由 Playbook Constraint `on_fail`（§23.2）、Human Review Policy（§26.1）、Conflict Handling 或 Guardrail 等多条路径触发。`requires_human_review = true` 为 OR 语义——任意路径触发即成立，来源记录在 `reasoning` 中，无需区分触发路径。

> **`require_review_on` 值来源（v0.1.8）：** 列表中混用两类来源：(1) Conflict Handling 冲突类型 key（如 `macro_regime_vs_playbook`），由 Conflict Handling 模块在步骤 8 产生；(2) 系统状态描述（如 `hard_constraint_insufficient_data`、`guardrail_block`），由 Constraint Evaluation / Guardrail 模块产生。规则引擎应在对应步骤完成后检查该步骤产出的条件是否匹配列表，匹配即触发。完整事件标识符体系由 SPEC-009 Governance 统一定义，MVP 由实现层保证名称一致性。

> **`macro_regime_vs_playbook` 无条件触发（v0.2.0）：** §36 中 `macro_regime_vs_playbook` 的 Conflict Handling 规则无 `condition`，语义为"只要此冲突类型出现即触发 `require_human_review`"。当宏观域 `domain_status = insufficient_data` 且未能生成可用 regime label 时，冲突是否"出现"取决于编排器是否能生成 Conflict Report——若编排器因缺少宏观域数据而不生成 `macro_regime_vs_playbook` 类型冲突，则规则不触发。**设计意图：宏观域数据缺失本身即为不确定性信号，需人工判断——但触发路径是 §8.4 第 3 条（若 4 个 Optional 域全缺）或编排器数据缺失事件，非 Conflict Handling 规则。** 详见 §8.4 NOTE。

> **`high_conflict` 判定标准（v0.1.9）：** `high_conflict` 的判定暂定为：`default_severity = high` 的 Conflict Handling 规则被实际触发（其 `actions` 被执行）时，视为 `high_conflict`。完整判定逻辑由 SPEC-009 统一定义，MVP 暂以此规则为准。

---

## 27. Output Policy

```json
{
  "output_policy": {
    "allow_strong_language": false,
    "must_show_opposing_evidence": true,
    "must_show_invalidating_conditions": true,
    "must_show_data_gaps": true,
    "must_show_playbook_version": true,
    "forbid_return_promise": true
  }
}
```

MVP 阶段，所有 Playbook 默认 `allow_strong_language = false`、`forbid_return_promise = true`。

---

## 28. Invalidating Conditions

> v0.1.1 修改：`impact` → `trigger_action`，区分触发阶段动作。

### 28.1 Schema

```json
{
  "invalidating_conditions": [
    {
      "condition_id": "growth_breakdown",
      "description": "收入增速低于行业中位数且连续两个季度恶化。",
      "input_refs": [
        "metric://revenue_growth_ttm",
        "metric://industry_median_revenue_growth_ttm"
      ],
      "trigger_action": "re_evaluate"
    },
    {
      "condition_id": "valuation_overextension",
      "description": "估值分位进一步升至极端高位。",
      "input_refs": ["metric://pe_percentile_5y"],
      "trigger_action": "avoid_new_position"
    }
  ]
}
```

> **`input_refs` MVP 阶段注释（v0.2.2）：** `invalidating_conditions` 的 `input_refs` 字段在 MVP 阶段仅供展示和人类阅读（详见 §28.3 NOTE），规则引擎不解析也不触发执行。实现者不应将 `input_refs` 的值用于运行时 metric 解析。

### 28.2 trigger_action 枚举

```text
re_evaluate
avoid_new_position
requires_human_review
reduce_confidence
notify_user
archive_condition
```

### 28.3 与 impact_on_decision 的区别

| 字段 | 阶段 | 含义 |
|---|---|---|
| `impact_on_decision` | Playbook Evaluation 当下 | 本次 Constraint 结果如何影响动作边界 |
| `trigger_action` | 未来失效条件触发时 | 未来发生该条件时系统应如何响应 |

> **MVP 执行性质（v0.1.2）：** Invalidating Conditions 在 MVP 阶段为前瞻性失效提示，不作为可自动检测的触发规则运行。`input_refs` 字段记录关联指标供人类阅读和未来系统自动检测使用。完整自动触发机制由后续 SPEC（Playbook Applicability Evaluator 或 SPEC-009 Governance）定义。当前版本中，`trigger_action` 值进入 Decision Trace，但不被规则引擎执行。

---

## 29. Versioning

每次 Playbook 执行必须记录版本信息。

```json
{
  "playbook_id": "capital_cycle_fundamental_playbook",
  "playbook_version": "0.1.0",
  "playbook_snapshot_hash": "sha256:...",
  "playbook_source": "built_in_static"
}
```

`snapshot_hash` 应基于 Playbook 执行逻辑相关字段生成（`applicability`、`constraints`、`preferences`、`freshness_requirements`、`conflict_handling`、`action_policy`、`human_review_policy`、`output_policy`、`invalidating_conditions`），排除纯 metadata 字段（`created_at`、`updated_at`、`created_by`），防止无意义的版本漂移。若内容发生实质变化，必须更新 `playbook_version`、`snapshot_hash`、`updated_at`。历史 Decision Trace 必须保留当时使用的 Playbook snapshot。

`playbook_source` 枚举：

```text
built_in_static
user_defined
imported
```

MVP 阶段仅使用 `built_in_static`。`user_defined`、`imported` 为未来扩展预留。

---

# Part A：默认 Playbook

## 30. capital_cycle_fundamental_playbook

### 30.1 定位

`capital_cycle_fundamental_playbook` 是 MVP 默认内置 Playbook。

面向：资本周期投资者、产业周期投资者、中长期基本面投资者、价值与成长结合型投资者、关注行业供需/资本开支/政策环境/估值周期的专业投资者。

不适用于：日内交易、短线情绪交易、纯技术分析交易、高杠杆投机、自动交易。

> **MVP 估值阈值适用范围（v0.1.5）：** 本 Playbook 的估值阈值（`pe_percentile_5y <= 0.8`）基于通用成长型股票校准，不适用于银行、保险、周期商品等 PB/ROE 驱动或重资产周期行业。如用于此类行业，建议配合行业专用 Playbook 使用。阈值是否应按行业调整为开放问题（§45 Q1），MVP 使用统一阈值。

---

## 31. 默认 Applicability

```json
{
  "asset_types": ["stock"],
  "investment_horizon": {
    "time_horizon_bucket": "medium_term",
    "time_horizon_days_min": 90,
    "time_horizon_days_max": 365
  },
  "supported_task_types": [
    "single_stock_buy_decision",
    "single_stock_hold_review",
    "single_stock_watchlist_review"
  ],
  "preferred_user_profile": [
    "capital_cycle_investor",
    "fundamental_investor",
    "industry_cycle_investor"
  ],
  "not_suitable_for": [
    "intraday_trading",
    "short_term_momentum_trading",
    "pure_sentiment_trading"
  ]
}
```

---

## 32. 默认 Required Domains

```json
{
  "required_domains": [
    {
      "domain": "fundamentals",
      "minimum_status": "completed",
      "on_missing": "analysis_incomplete"
    }
  ],
  "optional_domains": [
    {
      "domain": "macro_meso",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "company_event_catalyst",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "sentiment",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    },
    {
      "domain": "technical_market",
      "minimum_status": "partial",
      "on_missing": "continue_with_warning"
    }
  ]
}
```

---

## 33. 默认 Hard Constraints

### 33.1 财务质量未恶化

```json
{
  "constraint_id": "fundamental_quality_001",
  "name": "财务质量未恶化",
  "constraint_type": "hard",
  "evaluation_mode": "multi_rule",
  "condition_logic": "all",
  "rules": [
    {
      "rule_id": "gross_margin_not_deteriorating",
      "evaluation_mode": "ref_vs_threshold",
      "input_ref": "metric://gross_margin_qoq_change",
      "operator": ">=",
      "threshold": -0.05
    },
    {
      "rule_id": "fcf_margin_positive",
      "evaluation_mode": "ref_vs_threshold",
      "input_ref": "metric://fcf_margin_ttm",
      "operator": ">",
      "threshold": 0
    }
  ],
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "as_of_mismatch_policy": "note"
}
```

说明：允许毛利率小幅波动（下降 ≤ 5 百分点），且自由现金流率必须为正。

> **资本扩张期例外（v0.1.6）：** 当公司处于资本扩张周期（`growth_capex_flag = true`）时，`fcf_margin_ttm > 0` 子规则跳过。该子规则 status 设为 `not_applicable`，整体 Constraint 按剩余子规则计算——与 `not_applicable` 枚举语义一致（§17.2）。Decision Trace 须记录此例外。`growth_capex_flag` 由能力域在 `constraint_exports` 中导出。

### 33.2 收入增长不弱于行业

```json
{
  "constraint_id": "growth_vs_industry_001",
  "name": "收入增长不弱于行业",
  "constraint_type": "hard",
  "evaluation_mode": "ref_vs_ref",
  "left_ref": "metric://revenue_growth_ttm",
  "right_ref": "metric://industry_median_revenue_growth_ttm",
  "operator": ">=",
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "as_of_mismatch_policy": "note"
}
```

### 33.3 估值不过度昂贵

```json
{
  "constraint_id": "valuation_margin_001",
  "name": "估值不过度昂贵",
  "constraint_type": "hard",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["metric://pe_percentile_5y"],
  "operator": "<=",
  "threshold": 0.8,
  "on_fail": "block_new_position",
  "on_insufficient_data": "need_more_data",
  "on_stale_data": "need_more_data",
  "as_of_mismatch_policy": "note"
}
```

---

## 34. 默认 Soft Constraints

### 34.1 宏观环境不明显逆风

```json
{
  "constraint_id": "macro_environment_001",
  "name": "宏观环境不明显逆风",
  "constraint_type": "soft",
  "evaluation_mode": "multi_label_avoid",
  "input_refs": [
    "label://rate_environment",
    "label://liquidity_environment"
  ],
  "avoid_values": ["tightening", "contracting"],
  "match_policy": "all_refs_in_avoid_values",
  "on_fail": "require_human_review",
  "on_insufficient_data": "note"
}
```

### 34.2 市场情绪不过热

```json
{
  "constraint_id": "sentiment_overheat_001",
  "name": "市场情绪不过热",
  "constraint_type": "soft",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["label://sentiment_state"],
  "operator": "!=",
  "threshold": "overheated",
  "on_fail": "lower_confidence",
  "on_insufficient_data": "note"
}
```

### 34.3 技术状态不明显追高

```json
{
  "constraint_id": "technical_overextension_001",
  "name": "技术状态不明显追高",
  "constraint_type": "soft",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["metric://rsi_14d"],
  "operator": "<=",
  "threshold": 75,
  "on_fail": "lower_confidence",
  "on_insufficient_data": "note"
}
```

### 34.4 重大事件不处于低确定性状态

> v0.1.1 修正：`label://event_certainty` → `fact://any_material_event_low_certainty`。

```json
{
  "constraint_id": "event_certainty_001",
  "name": "重大事件不处于低确定性状态",
  "constraint_type": "soft",
  "evaluation_mode": "ref_vs_threshold",
  "input_refs": ["fact://any_material_event_low_certainty"],
  "operator": "!=",
  "threshold": true,
  "on_fail": "require_human_review",
  "on_insufficient_data": "note"
}
```

---

## 35. 默认 Preferences

```json
[
  {
    "preference_id": "prefer_margin_of_safety",
    "name": "偏好安全边际",
    "preference_type": "action_ranking",
    "priority": "high",
    "effect": "prefer_wait_over_buy_when_valuation_expensive"
  },
  {
    "preference_id": "avoid_chasing_overheated_sentiment",
    "name": "避免情绪过热时追高",
    "preference_type": "action_ranking",
    "priority": "medium",
    "effect": "prefer_add_to_watchlist_when_sentiment_overheated"
  },
  {
    "preference_id": "prefer_confirmed_fundamental_quality",
    "name": "偏好已确认的基本面质量",
    "preference_type": "confidence_adjustment",
    "priority": "high",
    "effect": "lower_confidence_when_fundamentals_partial"
  }
]
```

---

## 36. 默认 Conflict Handling

> v0.1.1 修正：拆分为可执行 `actions`。v0.1.3：`conflict_handling` 顶层为对象（key 为冲突类型），每种冲突类型只允许一条规则。若未来需要同类型多条规则（如不同 condition 的两条 `fundamentals_vs_valuation`），schema 应改为数组。

```json
{
  "macro_regime_vs_playbook": {
    "default_severity": "high",
    "actions": ["require_human_review"]
  },
  "fundamentals_vs_valuation": {
    "default_severity": "medium",
    "actions": ["prefer_wait"]
  },
  "sentiment_vs_valuation": {
    "default_severity": "high",
    "actions": ["lower_confidence", "prefer_wait"]
  },
  "technical_vs_fundamentals": {
    "default_severity": "medium",
    "condition": {
      "input_ref": "label://trend_state",
      "operator": "in",
      "values": ["downtrend", "trend_reversal"]
    },
    "actions": ["prefer_wait"]
  },
  "time_horizon_mismatch": {
    "default_severity": "low",
    "actions": ["note"]
  }
}
```

---

## 37. 默认 Freshness Requirements

> v0.1.1 修正：`pe_percentile_5y` 从 `daily` 改为 `quarterly`。

```json
[
  {
    "input_ref": "metric://revenue_growth_ttm",
    "freshness_level": "quarterly",
    "max_age_days": 120,
    "on_stale_data": "need_more_data"
  },
  {
    "input_ref": "metric://gross_margin_qoq_change",
    "freshness_level": "quarterly",
    "max_age_days": 120,
    "on_stale_data": "need_more_data"
  },
  {
    "input_ref": "metric://pe_percentile_5y",
    "freshness_level": "quarterly",
    "max_age_days": 120,
    "on_stale_data": "need_more_data"
  },
  {
    "input_ref": "metric://rsi_14d",
    "freshness_level": "daily",
    "max_age_days": 3,
    "on_stale_data": "flag"
  }
]
```

---

## 38. 默认 Human Review Policy

```json
{
  "require_review_on": [
    "high_conflict",
    "guardrail_block",
    "validation_block",
    "macro_regime_vs_playbook",
    "hard_constraint_insufficient_data",
    "major_company_event_with_low_certainty"
  ],
  "allow_decision_candidate_before_review": false
}
```

---

## 39. 默认 Output Policy

```json
{
  "allow_strong_language": false,
  "must_show_opposing_evidence": true,
  "must_show_invalidating_conditions": true,
  "must_show_data_gaps": true,
  "must_show_playbook_version": true,
  "forbid_return_promise": true
}
```

---

## 40. 默认 Invalidating Conditions

> v0.1.1 修正：`impact` → `trigger_action`。

```json
[
  {
    "condition_id": "growth_breakdown",
    "description": "收入增速低于行业中位数且连续两个季度恶化。",
    "input_refs": [
      "metric://revenue_growth_ttm",
      "metric://industry_median_revenue_growth_ttm"
    ],
    "trigger_action": "re_evaluate"
  },
  {
    "condition_id": "valuation_overextension",
    "description": "估值分位进一步升至极端高位。",
    "input_refs": ["metric://pe_percentile_5y"],
    "trigger_action": "avoid_new_position"
  },
  {
    "condition_id": "cashflow_deterioration",
    "description": "自由现金流率转负或显著恶化。",
    "input_refs": ["metric://fcf_margin_ttm"],
    "trigger_action": "re_evaluate"
  },
  {
    "condition_id": "major_negative_event",
    "description": "出现重大负面公司事件。",
    "input_refs": [
      "fact://any_material_negative_event_unresolved"
    ],
    "trigger_action": "requires_human_review"
  }
]
```

> **NOTE（v0.1.7）：** `cashflow_deterioration` 条件引用的 `fcf_margin_ttm` 在 `growth_capex_flag = true` 时不自动执行（与 §33.1 资本扩张期例外一致）。MVP 阶段 Invalidating Conditions 不自动运行（§28.3），此对应关系仅供人类阅读参考。

---

## 41. Playbook Evaluation 执行流程

MVP 阶段执行顺序：

```text
1. Load Playbook
2. Check Applicability
3. Resolve Required Domains（同时检查 Optional Domains 状态。若违反 §8.4 最小可用阈值，在此步将 `run_status` 设为 `analysis_incomplete`，不继续执行后续步骤）
4. Resolve input_refs from constraint_exports
5. Check data_freshness
6. Evaluate Hard Constraints
7. Evaluate Soft Constraints
8. Apply Conflict Handling Policy
9. Apply Preferences
10. Generate Playbook Evaluation Report
```

Playbook Evaluation 不直接调用能力域。它只消费已有 Analysis Cards 与 Conflict Reports。

---

## 42. 错误与降级策略

### 42.1 input_ref 无法解析

若关键 Hard Constraint 的 input_ref 无法解析：`status = insufficient_data`、`impact_on_decision = need_more_data`。

### 42.2 数据过期

若关键 Hard Constraint 数据过期：`status = stale_data`、`impact_on_decision = need_more_data`。

### 42.3 Soft Constraint 数据缺失

`status = insufficient_data`。`impact_on_decision` 设为 `neutral`（不影响动作边界），同时通过 Decision Trace 记录 `note` 类型注记。

### 42.4 Playbook 不适用

`applicability_status = not_applicable`、`overall_result = not_suitable_for_playbook`。

---

## 43. MVP 实现边界

MVP 必须实现：

1. 静态内置 Playbook；
2. Playbook Metadata；
3. Applicability 基础检查；
4. Required Domains 检查；
5. 四种 evaluation_mode 的 Hard Constraint Evaluation；
6. Soft Constraint Evaluation；
7. Preference 记录（`action_ranking` 类型：步骤 9 应用排序；`confidence_adjustment` 类型：MVP 阶段仅进入 Decision Trace 说明，不执行 confidence cap 修改）；
8. Freshness Requirements；
9. Conflict Handling（含 condition + actions 模式）；
10. Playbook Evaluation Report；
11. recommended_decision_bounds 聚合；
12. playbook_snapshot_hash；
13. Decision Trace 中展示 Playbook 版本和约束结果。

MVP 暂不实现：用户可视化编辑复杂 Playbook、多 Playbook 对比、Playbook Marketplace、Playbook 自动生成、Playbook 自动优化、Playbook Applicability Evaluator、组合级 Playbook、自动交易策略。

---

## 44. 后续 SPEC 依赖

1. SPEC-003：Agentic 投研工作流架构（Playbook 消费其核心对象定义）；
2. SPEC-004：五类分析能力域（Playbook 消费 Analysis Card 的 `constraint_exports`）；
3. SPEC-005：Capability Package 规范；
4. SPEC-007：Orchestration 与执行路径；
5. SPEC-008：Decision Trace 与 Observability；
6. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
7. SPEC-012：数据治理与用户私有数据。

---

## 45. 开放问题

1. `capital_cycle_fundamental_playbook` 的阈值是否应按行业调整 — **MVP 已决：使用统一阈值（pe_percentile_5y ≤ 0.8），不适用于银行/保险/周期商品行业（见 §30.1）**。行业专用阈值由未来 Playbook 扩展实现；
2. Metric Registry 应归入 SPEC-005 还是 SPEC-006 — **MVP 暂定：归 SPEC-005**。SPEC-006 只引用 `metric_id`，不负责定义 metric 的计算方式和元数据；
3. Playbook Applicability Evaluator 是否需要独立 SPEC；
4. 用户自定义 Playbook 是否允许引用 Interpreted Evidence — **MVP 暂定：允许引用，但系统自动将该 Constraint 降级为 Soft Constraint，并在 Decision Trace 中标注**。该降级机制由 SPEC-009 Governance 统一定义；
5. 多 Playbook 冲突时如何处理；
6. Playbook 是否支持组合级约束；
7. 用户历史交易行为是否应影响 Playbook Preference — **MVP 暂定：不引入**。Playbook Preference 完全由 Playbook 定义决定。用户行为数据由 SPEC-012 数据治理单独处理；
8. Conflict Handling 是否应支持同类型多条规则（条件不同）— MVP 暂定每种冲突类型只允许一条规则（对象格式）。若未来需要同类型多条规则，冲突处理 schema 应从对象改为数组。

---

## 46. v0.2.0 总结

SPEC-006 v0.2.0 定义了 Investment Playbook 的核心结构、执行语义与 MVP 默认 Playbook。

本版本完成：

1. Investment Playbook 的产品定位；
2. Playbook 顶层 schema；
3. risk_tolerance 字段；
4. Applicability；
5. Required / Optional Domains + on_missing 收敛；
6. Hard / Soft Constraint + Preference；
7. 四种 evaluation_mode（ref_vs_threshold / ref_vs_ref / multi_rule / multi_label_avoid）；
8. input_refs 解析规则 + label://event_certainty 多事件规则；
9. Constraint Evaluation Result（含 task_id / run_id）；
10. on_conflict 拆分为可执行 actions + condition；
11. impact_on_decision；
12. Action Policy；
13. Playbook Evaluation Report；
14. recommended_decision_bounds 聚合规则（重排）；
15. Freshness Requirements（pe_percentile_5y 修正）；
16. Conflict Handling；
17. Human Review Policy；
18. Output Policy；
19. Invalidating Conditions（trigger_action）；
20. Versioning；
21. 默认 `capital_cycle_fundamental_playbook`。

SPEC-006 的核心原则是：

```text
Playbook defines method.
Constraints encode judgment.
Evidence resolves constraints.
Bounds shape actions.
Trace preserves accountability.
```

中文表达：

```text
Playbook 定义方法；
约束编码判断；
证据解析约束；
边界塑造动作；
链路保留责任。
```
