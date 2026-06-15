# SPEC-005 Executable Specification

✅ **已实现** — Metric Registry Entry Pydantic v2 契约 + 边界测试 + JSON Schema。

## Scope

- `MetricRegistryEntry`: Pydantic v2 模型，含 determination_type 一致性校验。
- `FactRegistryEntry`: fact:// URI 格式校验。
- `LabelRegistryEntry`: label:// URI + allowed_values 校验。
- `DerivedMetricRuleTable`: 声明式规则表 + first-match 短路 + 强制 test_cases 覆盖。
- Confidence 规则: computed_default → 1.0, model_output → 需要 model_id, llm_interpreted → 禁止 hard_constraint。
- URI ref → metric_id 一致性校验。
- Extra fields forbidden。

## Run

```powershell
cd executable_specs/spec005
python -m pytest
python scripts/export_schema.py
```

## Normative Order

1. Functions in `src/crosslens_spec005/`.
2. Contracts in `src/crosslens_spec005/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-005).

## Source

- [SPEC-005 Capability Package 与 Metric Registry 规范](../../SPEC-005%20Capability%20Package%20与%20Metric%20Registry%20规范%20v0.2.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
