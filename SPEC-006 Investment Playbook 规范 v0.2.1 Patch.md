# SPEC-006：Investment Playbook 规范 v0.2.1 Patch

**版本：** v0.2.1 Patch  
**状态：** Review  
**项目名称：** crosslens  
**适用文档：** SPEC-006 Investment Playbook 规范 v0.2.0  
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.3  
**提交目的：** 修复 SPEC-006 v0.2.0 中规则引擎实现前需要关闭的执行语义细节。

---

## 0. 修订目标

本补丁不改变 SPEC-006 v0.2.0 的主架构，只修复以下实现前需要关闭的问题：

1. 修正 `multi_rule + condition_logic = any` 时 `partial` 的判定规则；
2. 收紧最小可用能力域规则，避免 `failed` / `skipped` 被误计入有效非 Fundamentals 域；
3. 为 `ref_vs_ref` 的 `as_of` mismatch 增加可配置处理策略；
4. 保持与 SPEC-003 v0.3.4、SPEC-004 v0.2.3 的接口语义一致。

---

## 1. 修正 `multi_rule + any` 的 partial 判定

### 1.1 问题

SPEC-006 v0.2.0 中，§17.2 对 `partial` 的解释可能与 §13.3 的 `multi_rule` 规则产生冲突。

正确语义应为：

```text
multi_rule + condition_logic = any：
只要任一可执行子规则 pass，整体即 pass。
```

因此，不能在已经存在子规则 `pass` 的情况下，仅因为其他子规则 `insufficient_data` 就把整体标记为 `partial`。

### 1.2 修正规则

对于：

```json
{
  "evaluation_mode": "multi_rule",
  "condition_logic": "any"
}
```

整体状态按以下顺序判断：

1. 若任一子规则 `status = pass`，则整体 `status = pass`；
2. 若无子规则 pass，且至少一个子规则 `status = fail`，同时至少一个子规则 `status ∈ {insufficient_data, stale_data, partial}`，则整体 `status = partial`；
3. 若所有子规则均为 `insufficient_data`、`stale_data` 或 `partial`，且没有 pass / fail，则整体 `status = insufficient_data`；
4. 若所有可执行子规则均 fail，则整体 `status = fail`；
5. 若所有子规则均 `not_applicable`，则整体 `status = not_applicable`。

### 1.3 示例

```json
{
  "condition_logic": "any",
  "sub_rule_results": [
    {"rule_id": "r1", "status": "pass"},
    {"rule_id": "r2", "status": "insufficient_data"}
  ],
  "constraint_status": "pass"
}
```

解释：`any` 语义下，已有一个子规则 pass，整体即 pass。

---

## 2. 修正最小可用能力域规则

### 2.1 问题

SPEC-006 v0.2.0 §8.4 中，最小可用能力域规则如果写成：

```text
至少一个非 Fundamentals 能力域 domain_status ≠ insufficient_data
```

会造成实现歧义，因为 `failed` 和 `skipped` 也满足 `≠ insufficient_data`，但它们不应被计入有效贡献。

### 2.2 修正规则

应改为：

```text
至少一个非 Fundamentals 能力域 domain_status ∈ {completed, partial}
```

### 2.3 完整 MVP 最小可用能力域规则

MVP 阶段，生成完整 Decision Candidate 前必须满足：

1. 至少 3/5 个能力域返回 `domain_status ∈ {completed, partial}` 的 Analysis Card；
2. Fundamentals Card 必须满足 Playbook 的 required domain 规则；
3. 至少一个非 Fundamentals 能力域满足 `domain_status ∈ {completed, partial}`；
4. 不存在 Block 级 Validation Finding；
5. Playbook 关键 Hard Constraint 可以判断，或其不可判断已被 Playbook Evaluation 明确处理为 `need_more_data` / `requires_human_review`。

### 2.4 说明

`failed`、`skipped`、`insufficient_data` 均不得计入最小可用能力域阈值。

---

## 3. 为 `ref_vs_ref` 增加 as_of mismatch policy

### 3.1 问题

SPEC-006 v0.2.0 §12.3 已要求 `ref_vs_ref` 比较前检查两个 ref 的 `data_freshness.as_of` 时间差。

但当前默认处理偏软，主要作为 Decision Trace NOTE。

对于 Hard Constraint，跨 ref 时间错配可能影响比较结论，应允许 Playbook 或 Run Config 配置处理策略。

### 3.2 新增字段

Playbook 可声明：

```json
{
  "as_of_mismatch_policy": "note"
}
```

### 3.3 枚举

```text
note
stale_data
require_human_review
```

### 3.4 语义

| as_of_mismatch_policy | 语义 |
|---|---|
| `note` | 记录到 Decision Trace，不改变 Constraint status |
| `stale_data` | 将该 Constraint 标记为 `stale_data` |
| `require_human_review` | 标记 Playbook Evaluation Report `requires_human_review = true` |

### 3.5 默认值

MVP 默认：

```text
as_of_mismatch_policy = note
```

### 3.6 Hard Constraint 建议

对于关键 Hard Constraint，Playbook 可以将其设置为：

```json
{
  "as_of_mismatch_policy": "stale_data"
}
```

或：

```json
{
  "as_of_mismatch_policy": "require_human_review"
}
```

### 3.7 与 overall_result 聚合关系

如果 `as_of_mismatch_policy = stale_data`，则该 Constraint 进入 `stale_data` 路径，并参与 SPEC-006 的 `overall_result` 聚合优先级。

如果同时存在另一个关键 Hard Constraint 明确 `fail`，则仍遵循：

```text
Hard Constraint fail > insufficient_data / stale_data
```

---

## 4. v0.2.1 Patch 总结

本补丁完成：

1. 明确 `multi_rule + any` 中任一 pass 即整体 pass；
2. 明确只有 `{completed, partial}` 可计入最小可用能力域阈值；
3. 明确 `failed` / `skipped` / `insufficient_data` 不可计入有效能力域贡献；
4. 为 `ref_vs_ref` 的 `as_of` 时间错配新增 `as_of_mismatch_policy`；
5. 保留 MVP 默认 `as_of_mismatch_policy = note`，同时允许 Hard Constraint 使用更强处理策略。

本补丁的核心原则是：

```text
Executable Playbook rules must not treat missing, failed, or skipped data as usable evidence.
```

中文表达：

```text
可执行 Playbook 规则不得把缺失、失败或跳过的数据当作可用证据。
```
