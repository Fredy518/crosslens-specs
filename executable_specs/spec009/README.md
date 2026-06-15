# SPEC-009 Executable Specification

> 📋 **计划中** — 尚未实现。

## Planned Scope

- Guardrail 规则引擎：6 条规则 + 边界收窄算法。
- Evaluator：四维质量检查（evidence_quality, reasoning_coherence, confidence_calibration, completeness）。
- `compute_final_confidence_cap`: Guardrail → Evaluator → Preference 三层合并。
- `resolve_decision_bounds`: 完整合并算法（Guardrail 收窄 → 污染检测 → confidence_cap → human_review 汇聚）。
- `check_evidence_contamination`: 递归 lineage 污染检测。
- 所有 action 枚举对齐 Registry `allowed_actions`（不得引入 `strong_buy`/`strong_sell`/`sell`/`reduce_position`）。

## Target Normative Order

实现后，规范优先级为：

1. Functions in `src/crosslens_spec009/`.
2. Contracts in `src/crosslens_spec009/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-009).

## Source

- [SPEC-009 Governance Guardrails Evaluator 与人工介入](../../SPEC-009%20Governance%20Guardrails%20Evaluator%20与人工介入%20v0.1.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
