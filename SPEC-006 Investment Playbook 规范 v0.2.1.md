# SPEC-006：Investment Playbook 规范

**版本：** v0.2.1

本文件合并 v0.2.0 与 v0.2.1 Patch。核心修复：

1. `multi_rule + condition_logic = any`：任一子规则 pass，整体 pass；
2. 最小可用能力域规则：只有 `domain_status ∈ {completed, partial}` 计入有效能力域；
3. `failed`、`skipped`、`insufficient_data` 不计入最小可用能力域阈值；
4. `ref_vs_ref` 增加 `as_of_mismatch_policy = note | stale_data | require_human_review`；
5. 默认 MVP 值为 `note`；关键 Hard Constraint 可设为 `stale_data` 或 `require_human_review`。

## 最小可用能力域规则

生成完整 Decision Candidate 前必须满足：

1. 至少 3/5 个能力域返回 `domain_status ∈ {completed, partial}` 的 Analysis Card；
2. Fundamentals Card 必须满足 Playbook 的 required domain 规则；
3. 至少一个非 Fundamentals 能力域满足 `domain_status ∈ {completed, partial}`；
4. 不存在 Block 级 Validation Finding；
5. Playbook 关键 Hard Constraint 可以判断，或其不可判断已被 Playbook Evaluation 明确处理为 `need_more_data` / `requires_human_review`。

## multi_rule + any

```text
1. 若任一子规则 status = pass，整体 status = pass；
2. 若无 pass，且存在 fail 与 {insufficient_data, stale_data, partial} 混合，整体 status = partial；
3. 若所有子规则均为 insufficient_data、stale_data 或 partial，且没有 pass/fail，整体 status = insufficient_data；
4. 若所有可执行子规则均 fail，整体 status = fail；
5. 若所有子规则均 not_applicable，整体 status = not_applicable。
```

## ref_vs_ref as_of_mismatch_policy

```json
{
  "as_of_mismatch_policy": "note"
}
```

语义：

| value | meaning |
|---|---|
| note | 记录到 Decision Trace，不改变 Constraint status |
| stale_data | 将该 Constraint 标记为 stale_data |
| require_human_review | 标记 Playbook Evaluation Report requires_human_review = true |

如果 `as_of_mismatch_policy = stale_data`，该 Constraint 进入 stale_data 路径，并参与 overall_result 聚合。

如果同时存在另一个关键 Hard Constraint 明确 fail，则仍遵循：

```text
Hard Constraint fail > insufficient_data / stale_data
```
