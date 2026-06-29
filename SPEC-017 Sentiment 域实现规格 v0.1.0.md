# SPEC-017：Sentiment 域实现规格

**版本：** v0.1.0  
**状态：** Draft  
**项目名称：** crosslens  
**文档类型：** 实现  
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.7；SPEC-005 v0.2；SPEC-006 v0.3.0；SPEC-007 v0.6；SPEC-016 v0.1.0
**目标阶段：** Sentiment P0 skeleton / 五域架构闭合

---

## 1. 文档目标

本 SPEC 定义 Sentiment 能力域 P0 骨架如何工作：如何消费结构化、可追溯、预评分的情绪/叙事 evidence，如何确定性输出 `AnalysisCard`，以及如何以 soft-only 方式提供 Playbook 可消费的叙事状态信号。

P0 目标不是实现完整情绪分析系统，而是让 CrossLens 五域架构闭合，使 `depth=deep` 在 mock/fixture baseline 或 reviewed real structured observations 下可以运行 fundamentals、technical_market、macro_meso、event_driven、sentiment 五张卡，并继续进入 conflict / playbook / governance / bounds / trace 阶段。真实路径在 source coverage 和治理通过前只属于 shadow validation。

---

## 2. 域目标与边界

Sentiment 域关注交易者预期与叙事状态，包括：

1. 叙事是否升温；
2. 市场是否形成一致预期；
3. 交易是否出现拥挤风险；
4. 正反馈和反身性是否强化；
5. 反方证据是否仍然可见；
6. 当前叙事状态对投资判断的 soft risk / soft support 含义。

Sentiment 域不负责：

1. 判断客观事件是否发生；
2. 验证催化剂是否真实改变基本面预期；
3. 判断价格趋势、放量、支撑阻力；
4. 生成买入、卖出、加仓、减仓等直接交易建议；
5. 在 P0 中执行跨平台情绪聚合、语义检索、实时监控、LLM 自动判断或社媒爬取。

---

## 3. 与其他域的区别

### 3.1 与 Event Driven 的区别

Event Driven 关注客观催化与预期差：

- 是否存在可追溯 source event；
- 事件是否改变价格、利润、订单、供需或政策约束；
- 事件如何映射到 A 股标的、行业、主题和受益链条；
- 事件后价格反应和可交易窗口。

Sentiment 关注叙事扩散和市场预期状态：

- 同一事件或主题是否已被市场反复讨论；
- 观点是否趋同；
- 是否存在拥挤交易和反身性风险；
- 反方证据是否仍然被看见；
- 叙事是否已经从“信息发现”进入“共识交易”或“拥挤退潮”。

### 3.2 与 Technical / Market 的区别

Technical / Market 关注价格行为确认：

- 趋势、动量、成交量、波动率和流动性；
- 威科夫、背离、支撑阻力、相对强度；
- A 股涨跌停、停牌、T+1 对可执行性的影响。

Sentiment 关注交易者预期与叙事状态：

- 叙事热度和一致预期；
- 拥挤和反身性；
- 反方证据可见度；
- 这些状态对 Playbook soft constraints 的提示作用。

Sentiment 不把“叙事热”解释为价格趋势确认；价格确认必须由 Technical / Market 域提供。

---

## 4. P0 输入

P0 只消费已经结构化、预评分、可追溯的 observations。fixture/mock baseline 用于 deterministic regression；真实 deep shadow path 只允许 reviewed structured JSON/JSONL，不接实时抓取、不做 LLM 判分，也不得用 fixture/mock 分数冒充真实情绪。

最小输入记录：

| 字段 | 类型 | 说明 |
|---|---|---|
| `evidence_id` | string | 可追溯 evidence id |
| `observation_date` | string | 观察日期，YYYYMMDD |
| `source_type` | string | fixture、research_note、market_commentary 等来源类型 |
| `narrative` | string | 叙事摘要，可为空 |
| `narrative_heat` | float 0~1 | 叙事热度 |
| `narrative_consensus` | float 0~1 | 一致预期程度 |
| `crowding_risk` | float 0~1 | 拥挤风险 |
| `reflexivity_risk` | float 0~1 | 反身性风险 |
| `contrary_evidence_visibility` | float 0~1 | 反方证据可见度 |
| `stance_signal` | enum | `positive` / `moderately_positive` / `neutral` / `mixed` / `moderately_negative` / `negative` |
| `confidence` | float 0~1 | 该条结构化 evidence 可信度 |
| `generation_type` | enum | P0 默认 `structured`；不得用 LLM interpreted 结果冒充 computed |
| `source_provider` | string | reviewed source provider；真实路径必填 |
| `source_url_or_document_id` | string | source URL 或内部 document id；真实路径必填 |
| `source_published_at_utc` | string | source 发布时间；必须不晚于 workflow `as_of` |
| `source_fingerprint` | string | 稳定 fingerprint，用于 trace / dedupe |

真实路径的 reviewed source validation 必须检查必填 lineage、日期窗口、0~1 metric 范围、`stance_signal` 值域，以及 source 字段中不得出现 fixture/mock 占位语义。未配置真实 source 时，adapter 返回 empty bundle / unavailable card，而不是混入 fixture/mock observations。

---

## 5. P0 输出

P0 必须返回合法 `AnalysisCard`，并复用 SPEC-004 的 schema：

- `domain = sentiment`
- `domain_status ∈ {completed, partial, unavailable}`
- `stance` 使用 SPEC-004 `Stance` 枚举
- `constraint_exports` 只允许 soft-only
- `domain_payload` 存放 runtime 字段和评分明细
- `warnings` / `limitations` 明确说明 P0 限制

P0 `domain_payload` 至少包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `narrative_heat` | float | 叙事热度聚合分 |
| `narrative_consensus` | float | 一致预期聚合分 |
| `crowding_risk` | float | 拥挤风险聚合分 |
| `reflexivity_risk` | float | 反身性风险聚合分 |
| `contrary_evidence_visibility` | float | 反方证据可见度聚合分 |
| `sentiment_stance` | string | Sentiment 域立场 |
| `observation_count` | int | 输入 observation 数量 |
| `p0_scope` | string | P0 范围声明 |

---

## 6. Deterministic Scoring

P0 scoring 必须 deterministic：

1. 对每个数值字段做 confidence-weighted average；
2. 输入为空时返回 `domain_status=unavailable`；
3. 输入存在但字段不足或 observation 数量不足时返回 `partial`；
4. 输入数量和字段覆盖充足时可返回 `completed`；
5. `crowding_risk >= 0.75` 或 `reflexivity_risk >= 0.75` 时，`sentiment_stance` 应优先降为 `mixed`；
6. `confidence` 上限不超过 P0 skeleton cap，避免把 fixture 情绪分数误读为强投资结论。

P0 不调用 LLM，不访问外部实时源，不做自然语言抽取。

---

## 7. Constraint Exports

P0 可导出以下 soft-only refs：

| export_ref | type | hard-capable | 说明 |
|---|---|:---:|---|
| `metric://narrative_heat` | metric | false | 叙事热度 |
| `metric://narrative_consensus` | metric | false | 一致预期 |
| `metric://crowding_risk` | metric | false | 拥挤风险 |
| `metric://reflexivity_risk` | metric | false | 反身性风险 |
| `metric://contrary_evidence_visibility` | metric | false | 反方证据可见度 |
| `label://sentiment_stance` | label | false | 情绪域立场 |

所有导出必须满足：

- `can_support_hard_constraint = false`
- `allowed_constraint_types = ["soft"]`
- `registration_status = unregistered_mvp_local`
- `lineage_constraint_failure = "sentiment_p0_soft_only"` 或等价原因

Sentiment P0 不得导出 hard buy / sell / add / trim 结论。

---

## 8. Orchestration 接入

P0 接入要求：

1. `JobDomain.SENTIMENT` 加入 `IMPLEMENTED_DOMAINS`；
2. `STANDARD_DOMAIN_ORDER` 保持 fundamentals、technical_market、macro_meso 三域不变；
3. `quick` 模式出现 sentiment / narrative / crowding / 情绪 / 叙事 / 拥挤 hint 时，可路由到 Sentiment；
4. `depth=deep` 在 Playbook 声明五域时，不应因 Sentiment pipeline 缺失 fail fast；
5. adapter 无 sentiment source 时，Context Builder 返回空 bundle，由 Sentiment card 降级为 `unavailable`。

---

## 9. P0 禁止事项

P0 明确禁止：

1. 不接真实社媒、新闻站、论坛、RSS 或行情实时源；
2. 不做跨平台情绪聚合；
3. 不做语义检索、embedding search 或相似事件召回；
4. 不做 LLM 自动分类或自动投资判断；
5. 不输出 hard constraint；
6. 不输出买入、卖出、加仓、减仓等直接动作建议；
7. 不覆盖 Event Driven 的 source event / catalyst 判断；
8. 不覆盖 Technical / Market 的价格行为确认。

---

## 10. P1 / P2 留待后续

P1 可扩展：

- 多来源结构化 sentiment source；
- 新闻/RSS/公告/研报摘要的人工或半自动标签导入；
- 叙事生命周期状态；
- 与 Event Driven source event 的显式关联。

P2 可扩展：

- 检索增强的叙事聚类；
- 小模型/LLM 辅助分类，但必须保留 source lineage 和人工可审计字段；
- 实时监控和去重；
- 拥挤风险与交易行为数据的联合校准。
