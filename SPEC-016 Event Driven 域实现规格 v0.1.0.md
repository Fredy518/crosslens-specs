# SPEC-016：Event Driven 域实现规格

**版本：** v0.1.0
**状态：** Draft
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.7；SPEC-005 v0.2；SPEC-006 v0.3.0；SPEC-014 v0.2.3
**实现参考：** SPEC-013 v0.2.0（消费者域 Pipeline 模式、Evidence 边界）；SPEC-015 v0.1.1（optional 域、confidence cap 与上游 CR 记录方式）
**上游契约：**
- SPEC-003 §6.4 (domain 枚举，event_driven)
- SPEC-003 §6.5 (Evidence Packet schema)
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-004 §23~§28 (Event Driven / Catalyst 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-004 §4 (Analysis Card 通用 Schema)
- SPEC-005 §5 (Metric / Fact / Label Registry)
- SPEC-005 §4.4 (Evidence Packet confidence 取值规则)
- SPEC-006 §18.3 (event_certainty 多事件解析规则)
- SPEC-006 §30 (MVP Playbook optional domains)
**目标阶段：** 域实现规格 / MVP 实现前置

---

## 0. 版本说明

### v0.1.0

首个 Draft 版本。将 Event Driven / Catalyst 域从“公司事件”扩展为“事件驱动策略工作流”的实现规格：事件发现、预期差判断、可交易窗口评估、受益链条映射、定价阶段识别、Analysis Card 组装、confidence、降级和验证规则。

本版本采纳的策略原则：

```text
发现事件 -> 判断事件是否改变预期 -> 评估可交易窗口
-> 找到最受益标的 -> 标记是否需要技术面确认
-> 输出风险、证伪条件和 Playbook 可消费的约束
```

Event Driven 域不直接生成买卖动作、不负责仓位和退出执行；这些由 SPEC-006 Playbook 与 Decision Candidate 层处理。

---

## 1. 文档目标

本 SPEC 定义 Event Driven / Catalyst 能力域**怎么做（HOW）**：如何消费事件类 Evidence，如何判断事件是否改变市场预期，如何映射受益链条，如何评估可交易性，如何生成 Analysis Card。

**不修改上游 WHAT 契约。** Event Driven 域的定义、输入、payload、constraint_exports、冲突类型和降级规则由 SPEC-004 §23~§28 定义。本 SPEC 只定义实现路径。若实现中发现上游契约缺口，记录在 §13 上游 CR 清单，不在本 SPEC 内直接修改上游 schema。

**可单测声明。** 本 SPEC 中的事件分类、评分、状态降级、confidence cap、constraint export 生成与 validation 规则均应可脱离 LLM 单元测试。LLM/Agentic reasoning 仅用于解释 `transmission_path`、补全候选链条和生成 summary，不得替代 source evidence、计算指标或 lineage 判定。

**消费者域定位。** Event Driven 域主要消费 Context & Evidence Layer 注入的事件、新闻、公告、价格、政策和产业链 evidence。域内可计算事件后收益、成交量反应、距事件天数、事件频率等 derived metrics，但不把这些内部计算结果回流共享 Evidence Pool，除非编排器显式发出 evidence request。

---

## 2. 域目标与边界

### 2.1 负责

Event Driven / Catalyst 域分析“事件是否会触发目标资产重新定价”。它关注：

1. 事件是否真实发生，来源是否可追溯；
2. 事件是否改变价格、利润、订单、供需、政策约束或估值预期；
3. 事件属于一次性刺激、中期催化还是可持续产业逻辑；
4. 事件能否映射到 A 股标的、行业、主题或同业组合；
5. 哪些标的是核心龙头、高弹性、补涨或业绩兑现角色；
6. 事件处于未发现、启动、扩散、加速、过度定价、退潮或证伪哪个阶段；
7. 事件需要哪些后续验证，哪些条件会使逻辑失效；
8. 是否需要 Technical / Market 域确认趋势、放量、板块联动或风险位置。

### 2.2 不负责

Event Driven / Catalyst 不负责：

1. 完整财务指标计算 -> Fundamentals 域；
2. 技术指标、支撑阻力、趋势确认 -> Technical / Market 域；
3. 市场情绪、叙事拥挤与社媒热度 -> Sentiment 域；
4. 宏观预测、流动性 regime -> Macro / Meso 域；
5. 最终买卖、仓位、加减仓和止损执行 -> Playbook + Decision Candidate 层；
6. 将传闻、解释性材料或低置信源直接当作 confirmed fact。

### 2.3 跨域边界

| 边界 | 归属 | 说明 |
|---|---|---|
| 事件是否发生 | Event Driven | 必须有 source evidence、event_date、certainty |
| 财务影响规模 | Fundamentals + Event Driven | Fundamentals 提供财务基线；Event Driven 判断事件造成的 `expectation_delta` |
| 技术面确认 | Technical / Market | Event Driven 只输出 `requires_technical_confirmation` 或引用已有市场反应指标 |
| 情绪拥挤 | Sentiment | Event Driven 可记录“资金扩散/加速”线索，但不独立判断情绪拥挤 |
| 买入/卖出/仓位 | Playbook | Event Driven 只给事件质量、可交易性和失效条件 |

### 2.4 A 股适配

A 股事件驱动尤其关注：

1. 涨价函、产品调价、库存低位、供给收缩；
2. 停产检修、环保限产、海外工厂事故、出口管制；
3. AI / 算力需求外溢、国产替代、客户验证、订单爆发；
4. 业绩预告、财报超预期、毛利率改善、订单延续；
5. 政策文件、产业会议、采购计划、财政补贴、强制标准；
6. 并购重组、资产注入、央国企整合、控制权变更；
7. 海外龙头业绩、涨价、扩产、订单指引对 A 股产业链的映射；
8. 板块异动、龙头确认、扩散到补涨标的、末端乱炒等资金阶段。

---

## 3. Evidence Consumption Catalog

### 3.1 Evidence 类型与必需性

| # | evidence_type | generation_type | determinism_level | can_support_hard | 必需性 | 说明 |
|---|---|---|---|:---:|---|---|
| 1 | `event_driven` | structured | structured | false | required | 事件容器或统一事件入口 |
| 2 | `company_event` | structured | structured | false | optional | 公司自身事件 |
| 3 | `industry_catalyst_event` | structured | structured | false | optional | 行业新闻、供需、涨价、产业链变化 |
| 4 | `policy_catalyst_event` | structured | structured | false | optional | 政策、监管、审批、补贴、强制标准 |
| 5 | `cross_market_catalyst_event` | structured | structured | false | optional | 海外映射、跨市场龙头事件 |
| 6 | `commodity_or_supply_shock_event` | structured/computed | structured/computed | false | optional | 商品价格、供给事故、出口管制 |
| 7 | `earnings_release_event` | structured | structured | false | optional | 财报、业绩预告、业绩快报 |
| 8 | `post_event_price_reaction` | computed | computed | true | optional | 事件后收益、成交量反应 |
| 9 | `beneficiary_chain_map` | structured | structured | false | optional | 产业链与受益标的映射 |

**必需性裁决：**

- 至少需要 1 条可追溯的 source event（`event_driven` 或任一具体事件 evidence），否则 `domain_status = unavailable`。
- 只有 interpreted evidence 且无 source reference 时，`domain_status = unavailable`。
- 有 source event 但缺少目标映射、预期影响或事件日期时，`domain_status = partial`。
- 有 confirmed/partially_confirmed source event、目标映射、预期影响、风险/证伪条件，并能完成主要 validation 时，最高可为 `completed`。

### 3.2 事件类型归一化

Event Driven runtime 应将上游多源事件统一映射到以下 `catalyst_family`：

| catalyst_family | 典型事件 | 主要预期影响 |
|---|---|---|
| `price_profit_change` | 涨价、毛利率改善、业绩超预期 | 价格、利润、盈利预期 |
| `supply_constraint` | 停产、限产、事故、出口管制 | 供需平衡、价格上行 |
| `demand_acceleration` | 订单爆发、AI/算力需求、客户验证 | 收入、产能利用率 |
| `policy_regulatory` | 补贴、强制标准、审批、监管变化 | 需求释放或供给限制 |
| `domestic_substitution` | 国产招标、进入供应链、进口替代率提升 | 远期空间 + 中期订单 |
| `earnings_surprise` | 业绩预告/财报超预期 | 预期上修、估值重估 |
| `corporate_action` | 并购重组、资产注入、控制权变更 | 资产价值或治理变化 |
| `cross_market_mapping` | 海外龙头涨价、扩产、业绩指引 | 产业链映射和估值联动 |
| `theme_or_concept` | 会议提法、概念刺激、远期叙事 | 情绪或主题交易 |
| `rumor_or_noise` | 未证实传闻、低可信渠道 | 不得支撑强建议 |

### 3.3 事件强度排序

MVP 默认强度排序如下，用于 `impact_strength_score` 的先验：

```text
价格/利润变化 > 供需格局变化 > 订单/需求变化
> 政策/监管变化 > 概念/主题刺激 > 传闻
```

该排序只是先验。最终强度必须结合 source reliability、event_certainty、目标映射、价格反应和后续验证条件计算。

---

## 4. Pipeline

```text
Step 1  Input filtering & as_of cutoff
Step 2  Event normalization & deduplication
Step 3  Source reliability and event certainty resolution
Step 4  Catalyst classification
Step 5  Expectation-delta assessment
Step 6  Target mapping and beneficiary-chain construction
Step 7  Tradability scoring and pricing-stage classification
Step 8  Stance and confidence computation
Step 9  Analysis Card assembly and constraint_exports
Step 10 Domain validation and downgrade
Step 11 Summary / key_findings / limitations
```

### 4.1 Step 1：Input filtering & as_of cutoff

所有事件必须满足：

1. `event_date <= as_of_date`；
2. `source_published_at <= as_of_date`；
3. 若计算事件后价格反应，只能使用 `trade_date <= as_of_date` 的行情；
4. 若事件来自海外市场，使用当地时区的发布时间折算到 A 股可交易日。

不满足上述条件的事件必须剔除，并记录 `future_event_leakage_blocked`。

### 4.2 Step 2：Event normalization & deduplication

多源事件需按以下键去重：

```text
dedup_key = normalized_event_type
          + source_entity
          + event_date
          + normalized_target_scope
          + primary_source_hash
```

若同一事件来自多个 source，保留 source 列表，`source_reliability_score` 取加权平均，并优先使用官方公告、交易所公告、政策原文、价格数据或结构化数据源。

### 4.3 Step 3：Source reliability and certainty

`event_certainty` 的 resolution：

| source 状态 | event_certainty |
|---|---|
| 官方公告/政策原文/交易所披露/可核验价格数据 | confirmed |
| 多个可靠媒体或产业渠道交叉验证 | partially_confirmed |
| 单一媒体、社媒、未验证产业链反馈 | rumor |
| 来源缺失或不可追踪 | unknown |

### 4.4 Step 4：Catalyst classification

每条事件必须分类出：

```text
event_type
event_scope
target_scope
catalyst_family
catalyst_direction
catalyst_timing
event_materiality
event_certainty
event_resolution_status
```

若 `event_scope != company_specific`，必须填写 `source_entity`、`target_universe` 或 `target_scope`，并给出 `transmission_path`。

### 4.5 Step 5：Expectation-delta assessment

`expectation_delta_score` 衡量事件是否改变市场预期，而不是事件本身是否“看起来重要”。

| 评分维度 | 取值 | 说明 |
|---|---:|---|
| price_or_profit_impact | 0~1 | 是否直接改变价格、利润、毛利率 |
| supply_demand_impact | 0~1 | 是否改变供需、库存、产能利用率 |
| order_or_customer_impact | 0~1 | 是否带来订单、客户验证、需求确认 |
| policy_force | 0~1 | 是否有强制标准、补贴、采购计划、明确时间表 |
| prior_expectation_gap | 0~1 | 市场是否低估或尚未充分交易 |

```text
expectation_delta_score =
  0.30 * price_or_profit_impact
+ 0.25 * supply_demand_impact
+ 0.20 * order_or_customer_impact
+ 0.15 * policy_force
+ 0.10 * prior_expectation_gap
```

枚举映射：

| score | expectation_delta |
|---:|---|
| >= 0.75 | strong |
| >= 0.50 | moderate |
| >= 0.25 | weak |
| < 0.25 | none |

### 4.6 Step 6：Target mapping and beneficiary chain

受益链条必须先拆产业链，再映射标的。`beneficiary_chain` 至少包含：

```json
{
  "target_id": "002xxx.SZ",
  "target_name": "示例公司",
  "target_scope": "single_stock",
  "chain_segment": "CCL / 覆铜板",
  "beneficiary_role": "leader",
  "relevance_score": 0.82,
  "earnings_elasticity_score": 0.65,
  "price_elasticity_score": 0.58,
  "evidence_refs": ["ev_event_001", "ev_chain_map_001"]
}
```

`beneficiary_role` 取值：

```text
leader
high_beta
catch_up
earnings_realization
indirect
low_relevance
unknown
```

候选标的优先级不是公司质地本身，而是：

```text
event_relevance * earnings_elasticity * price_elasticity
* fund_recognition * technical_position_proxy
```

其中 `technical_position_proxy` 只能使用已有 market reaction 或 Technical 域输出；Event Driven 域不得自行计算技术指标。

### 4.7 Step 7：Tradability scoring and pricing stage

`tradability_score` 为 0~10 分：

| 维度 | 权重 | 说明 |
|---|---:|---|
| novelty_score | 0.15 | 事件是否刚发生或刚扩散 |
| expectation_delta_score | 0.20 | 是否改变预期 |
| persistence_score | 0.15 | 是否连续催化或可验证 |
| target_clarity_score | 0.15 | 是否能映射到明确 A 股标的 |
| earnings_elasticity_score | 0.10 | 是否能反映到利润 |
| market_reaction_score | 0.10 | 是否已有板块/成交反应 |
| fund_recognition_score | 0.05 | 是否出现龙头、成交放大或机构关注 |
| risk_reward_score | 0.10 | 是否尚未充分定价 |

```text
tradability_score = 10 * weighted_sum(dimensions)
```

分桶：

| score | tradability_bucket | 解释 |
|---:|---|---|
| >= 8.0 | high | 重点跟踪，可进入 Playbook 评估 |
| >= 6.0 | medium | 等待确认或低吸窗口 |
| >= 4.0 | low | 观察，不急于行动 |
| < 4.0 | noise | 多数情况下是噪音 |

`pricing_stage` 取值：

```text
undiscovered
initial_repricing
leader_confirmed
diffusion
acceleration
overextended
fading
invalidated
unknown
```

### 4.8 Step 8：Stance

Event Driven stance 由 `catalyst_direction`、`expectation_delta_score`、`tradability_score`、`pricing_stage` 和风险/证伪条件共同决定。

默认规则：

| 条件 | stance |
|---|---|
| 正向事件 + strong delta + score >= 8 + 未过度定价 | positive |
| 正向事件 + moderate delta + score >= 6 | moderately_positive |
| 正负事件混杂或事件与定价阶段冲突 | mixed |
| 负向事件 + high materiality + unresolved | negative / moderately_negative |
| 事件低确定性或无目标映射 | unavailable / neutral |

若 `pricing_stage = overextended`，正向事件最高只能到 `moderately_positive`，并写入 `warnings += ["event_overpriced_risk"]`。

---

## 5. Domain Payload

### 5.1 payload 顶层结构

```json
{
  "event_list": [],
  "catalyst_direction": "positive",
  "catalyst_strength": "medium",
  "catalyst_timing": "near_term",
  "expectation_delta": "moderate",
  "expectation_delta_score": 0.62,
  "tradability_score": 6.8,
  "tradability_bucket": "medium",
  "pricing_stage": "leader_confirmed",
  "beneficiary_chain": [],
  "requires_technical_confirmation": true,
  "event_risks": [],
  "invalidating_events": [],
  "limitations": []
}
```

### 5.2 event_list 扩展字段

每条 `event_list[]` 至少包含：

```text
event_type
event_scope
event_date
event_direction
event_materiality
event_certainty
event_resolution_status
source_entity
target_scope
target_universe
transmission_path
expected_time_horizon
source_evidence_ref
```

### 5.3 invalidating_events

`invalidating_events` 必须可操作，避免空泛表述。示例：

```text
产品涨价未延续
订单不及预期
政策落地弱于预期
公司澄清无相关业务
龙头成交放大但价格滞涨
事件后三个交易日板块无扩散
```

---

## 6. Constraint Exports

### 6.1 已允许 hard-capable 的 Computed Event metrics

遵从 SPEC-004 §26：

```text
metric://post_event_1d_return
metric://post_event_volume_vs_20d_average
metric://days_since_event
metric://event_frequency_90d
```

这些 metric 只有在以下条件全部满足时，才可 `can_support_hard_constraint = true`：

1. source event 可追溯；
2. source event `event_certainty = confirmed`；
3. source event 的 generation_type 非 `interpreted`；
4. 计算使用的数据未越过 `as_of_date`；
5. `registration_status = registered`。

### 6.2 Proposed soft-only exports

以下 export 在 v0.1.0 中仅允许 soft，不得支撑 Hard Constraint，除非后续 SPEC-005 注册：

```text
metric://tradability_score
metric://expectation_delta_score
metric://target_clarity_score
metric://earnings_elasticity_score
label://pricing_stage
label://catalyst_family
label://beneficiary_role
fact://requires_technical_confirmation
fact://event_overpriced_risk
```

### 6.3 事件标签禁用 hard

以下标签即使来自官方公告，也不得直接支撑 Hard Constraint：

```text
industry_catalyst_identified
policy_catalyst_identified
cross_market_catalyst_identified
management_guidance_raised
product_launch_confirmed
capital_return_announced
```

原因：这些标签需要抽取、分类和解释。让 Event Driven 域自行判断“自己输出的标签足够可靠并可硬约束”会形成循环自证。

---

## 7. Confidence

### 7.1 Raw confidence

```text
raw_confidence =
  0.30 * evidence_confidence_avg
+ 0.20 * source_reliability_score
+ 0.20 * target_mapping_confidence
+ 0.15 * pricing_data_confidence
+ 0.15 * completeness_factor
```

### 7.2 Certainty cap

| event_certainty | cap |
|---|---:|
| confirmed | 0.85 |
| partially_confirmed | 0.60 |
| rumor | 0.35 |
| unknown | 0.25 |

若一张卡包含多个事件，使用主事件的 certainty cap；主事件选择规则同 SPEC-006 §18.3。

### 7.3 Status cap

| domain_status | cap |
|---|---:|
| completed | 0.85 |
| partial | 0.60 |
| unavailable | 0.25 |
| error | 0.00 |

### 7.4 Interpreted evidence cap

如果主事件仅由 interpreted evidence 支撑，confidence 最高 0.40，且不得输出 hard-capable metric。

---

## 8. Domain Status

| 条件 | domain_status | reason |
|---|---|---|
| 无可追溯事件证据 | unavailable | insufficient_data |
| 只有 interpreted evidence 或 rumor | unavailable / partial | insufficient_data |
| 有事件但缺 event_date / target mapping / expectation_delta | partial | insufficient_data |
| 有 confirmed/partial event + 目标映射 + scoring + validation 通过 | completed | null |
| Pipeline 异常 | error | execution_failure |

`domain_status = completed` 不表示事件“值得交易”，只表示 Event Driven 域完成了事件识别、影响判断、映射和风险披露。

---

## 9. Domain Validation

必须执行以下检查：

| # | 检查 | 失败处理 |
|---|---|---|
| 1 | source_evidence_ref 缺失 | unavailable 或 partial |
| 2 | event_date / source_published_at 晚于 as_of | 剔除事件 + warning |
| 3 | rumor 被标记为 confirmed | 降级 certainty + warning |
| 4 | event_scope 与 target_scope 不一致 | partial + warning |
| 5 | 无 target_universe 且 target_scope 非 market | partial |
| 6 | transmission_path 为空 | partial |
| 7 | 仅概念刺激但 tradability_score >= 8 | cap score <= 5 |
| 8 | overextended 但 stance = positive | 降级 stance |
| 9 | hard export 缺 lineage 或非 confirmed | 降级为 soft |
| 10 | post-event metric 使用 future price | block export + warning |

---

## 10. Adapter / Context Builder 要求

Event Driven 域本身不直接抓取外部网站。Context & Evidence Layer 或 Adapter 需提供以下能力：

```python
get_event_feed(target, start_date, end_date)
get_industry_catalyst_events(industry_code, start_date, end_date)
get_policy_catalyst_events(industry_code, start_date, end_date)
get_cross_market_events(theme_or_industry, start_date, end_date)
get_commodity_or_supply_shock_events(industry_code, start_date, end_date)
get_post_event_price_reaction(targets, event_date, as_of_date)
get_beneficiary_chain_candidates(event, target_scope, as_of_date)
```

MVP 可先用结构化 fixture / mock adapter 验证 pipeline。真实数据接入时必须记录：

1. source provider；
2. source URL / table / document id；
3. source_published_at；
4. ingestion_time；
5. as_of_date；
6. target mapping 的规则版本。

---

## 11. Playbook 边界

Event Driven 域输出的是“事件是否形成可交易催化”的证据，不输出最终动作。

| Event Driven 输出 | Playbook 解释 |
|---|---|
| `tradability_bucket = high` | 可进入 playbook 评估，不等于 buy |
| `requires_technical_confirmation = true` | 需等待 Technical / Market 支持 |
| `pricing_stage = overextended` | 降低 allowed_actions 或要求人工复核 |
| `event_certainty != confirmed` | 不得强建议，可能 requires_human_review |
| `invalidating_events` 命中 | reduce / avoid / requires_human_review 由 Playbook 决定 |

---

## 12. Testability

### 12.1 单元测试

| 模块 | 测试重点 |
|---|---|
| event normalization | 多源事件去重、source hash、时间字段 |
| certainty resolution | confirmed / partial / rumor / unknown 映射 |
| catalyst classification | event_type / event_scope / catalyst_family |
| expectation scoring | 各维度权重和阈值 |
| target mapping | beneficiary_role、relevance、低相关度降级 |
| tradability scoring | 0~10 分、bucket、overextended cap |
| confidence | certainty cap、status cap、interpreted cap |
| exports | hard lineage 条件、soft-only proposed exports |
| validation | future leakage、rumor_as_fact、missing_target |

### 12.2 集成测试

MVP 至少覆盖：

1. confirmed price-increase event -> completed card；
2. cross-market catalyst -> target_scope=industry/theme；
3. rumor-only event -> partial/unavailable, no hard exports；
4. event already overextended -> positive stance capped；
5. event with no A 股 mapping -> partial；
6. post-event metrics as_of cutoff -> no future leakage。

---

## 13. 上游 CR 清单

### CR-016-001：SPEC-004 payload 字段扩展

- **现状：** SPEC-004 已定义 `event_scope`、`target_scope`、`transmission_path` 的基本方向，但未完整列出 `catalyst_family`、`tradability_score`、`pricing_stage`、`beneficiary_chain`。
- **裁决：** 本 SPEC 将这些作为 Event Driven runtime 的 domain_payload 扩展字段；若 SPEC-004 后续收紧 payload schema，应同步纳入。

### CR-016-002：SPEC-005 注册 proposed soft-only exports

- **现状：** `tradability_score`、`expectation_delta_score`、`pricing_stage` 等尚未进入 Registry。
- **裁决：** v0.1.0 全部 soft-only，不得支撑 Hard Constraint。后续如需 Playbook 直接引用，向 SPEC-005 提注册请求。

### CR-016-003：SPEC-006 Playbook 事件驱动动作模板

- **现状：** Playbook 已能消费事件 facts，但未定义“事件确认 -> 技术确认 -> 风险收益检查”的通用模板。
- **裁决：** Event Driven 域只输出证据与 flags；是否买入、等待、低吸、退出由 SPEC-006 后续扩展。

---

## 14. MVP 不交付

1. 不做自动网页爬取和非结构化全网新闻监控；
2. 不做实时推送；
3. 不做自动下单、仓位控制或止损执行；
4. 不做未经验证的产业链知识图谱自动生成；
5. 不把社媒热度当作事件真实性证据；
6. 不做分钟线/Tick 级事件交易；
7. 不从单一历史样本中学习事件权重并直接推广。
