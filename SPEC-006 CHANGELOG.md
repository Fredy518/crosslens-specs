# SPEC-006 Changelog

本文件归档 SPEC-006 的详细版本记录。SPEC 正文仅保留最近版本摘要。

## v0.3.0

1. 新增 Python Executable Specification，覆盖 multi-rule、overall-result、动作边界与 confidence-cap 合并。
2. 新增 Pydantic v2 契约和生成的 JSON Schema。
3. 新增边界测试，明确 ambiguous label、Soft fail、all-not-applicable、cap 阈值等行为。
4. `not_passed_for_add_position` 增加正式决策分支。
5. 明确 `partially_passed` 不自动移除 `buy`。
6. MVP Hard fail 的 impact 限定为 block-new、block-add 或 human-review。
7. 新增代码、契约、测试、Schema 与 Markdown 的职责及发布一致性要求。

## v0.2.9

1. 重写 `multi_rule + any` 状态优先级：任一 pass 即 pass，fail 与未决状态并存时为 partial，仅全量明确 fail 时为 fail。
2. 明确 Soft fail 全量计数与规则 1 首匹配短路。
3. 明确 confidence cap 中间值和最终阈值检查。
4. 增加 `constraint_exports` 字段缺失及版本不兼容 fallback。
5. 将 derived fact 生产契约移至 SPEC-004 v0.2.5，并补齐 boolean `fact_value` 消费规则。
6. 补齐 snapshot hash canonicalization 与外部依赖快照。
7. 明确 Preference 非加性排序。
8. 移除 `none`、将 freshness `flag` 改为 `dt_note`、拆分两类周期错配。

## v0.2.8

1. `confidence_cap < 0.5` 检查归属 Resolved Decision Bounds 阶段，不改写 Playbook Evaluation Report 的 `overall_result`。
2. §22.3 将至少一条 Hard `pass` 与 all-not-applicable 拆为显式互斥 guard。
3. §8.4 将关键 Hard Constraint 可判断条件改为机器可执行定义。
4. §4.2 增加 `invalidating_conditions` 双来源规则的就近引用。
5. `partially_applicable` 在 MVP 中改为保留枚举，系统不得主动产生。
6. Hard Constraint 的数据缺失和过期缺省值统一为 `need_more_data`。
7. 默认 Constraint 增加 Schema Validation 自检表。
8. 宏观域缺失只产生 Decision Trace 警告；实际宏观冲突才触发人工复核。

## v0.2.7

1. `confidence_cap` 多来源叠加低于 0.5 时增加人工复核保护。
2. 宏观域缺失增加保底人工复核路径。
3. `invalidating_conditions` 增加 Playbook 与 Analysis Card 双来源展示规则。
4. Applicability 周期偏离阈值设为 `time_horizon_days_min` 的 50%。
5. 明确多 Playbook 与组合级 Playbook 扩展不向后兼容。
6. §8.4 Fundamentals 可用状态收紧为 `{completed, partial}`。

## v0.2.6

1. 补齐 Soft Constraint stale 缺省行为。
2. 明确 all-not-applicable 不构成 vacuous pass。
3. 明确 `requires_human_review` 触发后不短路。
4. 明确多来源 confidence cap 下调采用叠加语义。

## v0.2.5

收紧 Soft Constraint 默认 evidence types 和有效 Analysis Card 状态；明确 all-not-applicable 不等于 passed；增加宏观域数据缺失 hook。

## v0.2.4

关闭 need_more_data 与 fail 优先级、ambiguous_label_ref 来源、all-not-applicable 交叉引用、partially_applicable MVP 语义、time_horizon_mismatch、as_of_mismatch、condition 降级、environment 枚举和动作映射等缺口。

## v0.2.3

补齐 `partial` 的 fail 优先判定、all-not-applicable 显式规则、Conflict Handling condition 降级顺序、ambiguous_label_ref 非短路、决策树门控、`re_evaluate` 枚举和 draft 开发工作流。

## v0.2.2

补齐决策树 need_more_data 限定、ambiguous_label_ref 来源区分、all-not-applicable 路径、partially_applicable 行为、as_of_mismatch_policy、环境枚举和动作映射说明。

## v0.2.1

修正 `multi_rule + any` 的 fail 优先判定，收紧 §8.4 有效域状态，并引入 `as_of_mismatch_policy`。

## v0.2.0

状态由 Review 升级为 Approved。修正 `partial` 触发条件，新增 MVP `conflict_type`、`priority`、confidence cap 下调规则、宏观冲突处理与 metadata/hash 边界。

## v0.1.9

补齐“所有 Hard pass”的判断标准、`partial` Analysis Card 的影响、Company Event derived fact 生产者、Freshness 到 Hard Constraint 的 stale 标记传递和 `high_conflict` 判定。

## v0.1.8

补齐 `multi_rule + any` 数据不足、决策表优先级、`multi_label_avoid` 部分解析、boolean threshold、`default_severity`、`require_review_on` 值来源和 `domain_status` 交叉引用。

## v0.1.7

补齐 `partial` 不执行 `on_fail`、Conflict Handling condition 降级保护、资本扩张例外、人工复核 OR 语义、confidence cap 可配置性、Preference 冲突规则和 Hard Constraint 引用边界。

## v0.1.6

补齐 Soft fail 计数、condition input_ref 降级、人工复核优先级、资本扩张例外、`operator: in`、Preference effect、`passed_with_caution` 动作边界和 Resolved Decision Bounds 合并方向。

## v0.1.5

修复默认 Conflict Handling 与 Hard Constraint 去重、`passed_with_caution` 聚合、Preference MVP 执行、Soft 数据缺失、label 值域来源和行业统一阈值立场。

## v0.1.4

补齐 blocking condition 去重、Soft Constraint 缺省行为、Optional Domain 优先级、as_of flag、multi_label_avoid AND 语义和 Preference confidence adjustment。

## v0.1.3

修复 `on_hard_constraint_fail` 分工、Conflict Handling ranking、ref_vs_ref freshness 取值和默认示例。

## v0.1.2

状态由 Draft 升级为 Review。统一 `input_refs` / `input_ref` 字段，修正 multi_label_avoid，明确 overall_result 优先级、事件 fact、Soft evidence 缺省、跨域 as_of 检查和 Invalidating Conditions MVP 性质。

## v0.1.1

补齐四种 evaluation mode、on_missing/on_conflict 枚举、事件 label 多值解析、Invalidating Conditions trigger_action、freshness、Constraint Evaluation Result 标识、Metadata 关系、risk_tolerance 和推荐边界聚合。
