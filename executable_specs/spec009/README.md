# SPEC-009 Executable Specification

✅ **已实现** — GuardrailReport, EvaluationReport, ResolvedDecisionBounds Pydantic v2 契约 + 边界测试 + JSON Schema。

## Scope

- `apply_guardrails`: 6 条 Guardrail 规则决策树（R1–R6），含 block_output control flag。
- `narrow_bounds`: 从 Playbook bounds 中移除 blocked_candidate_actions，fallback 到 wait。
- `run_evaluator`: 四维质量检查（evidence_quality, reasoning_coherence, confidence_calibration, completeness）。
- `compute_final_confidence_cap`: Guardrail → Evaluator → Preference 三层 cap 合并（单向收窄）。
- `aggregate_human_review_signals`: 六来源信号汇聚（Guardrail, Conflict, Playbook, Cap, Macro, Fundamentals）。
- `route_after_human_review`: block_candidate / proceed_to_candidate 路由。
- `check_evidence_contamination`: 递归 lineage 污染检测（max_depth=3）。
- `resolve_decision_bounds`: 六步完整合并算法。
- `ResolvedDecisionBounds` 模型级校验：forbidden_combinations, block_output/strong_buy/strong_sell/sell/reduce_position 硬禁止。
- 所有 action 枚举对齐 Registry `allowed_actions`。

## Run

```powershell
cd executable_specs/spec009
python -m pytest
python scripts/export_schema.py
```

## Normative Order

1. Functions in `src/crosslens_spec009/decision_logic.py`.
2. Contracts in `src/crosslens_spec009/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-009).

## Source

- [SPEC-009 Governance Guardrails Evaluator 与人工介入](../../SPEC-009%20Governance%20Guardrails%20Evaluator%20与人工介入%20v0.1.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
