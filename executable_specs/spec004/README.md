# SPEC-004 Executable Specification

✅ **已实现** — Analysis Card Pydantic v2 契约 + 边界测试 + JSON Schema。

## Scope

- `AnalysisCard`: Pydantic v2 模型，含 8 项 post-card validation rules（SPEC-004 §41）。
- `ConstraintExport`: 多态结构（metric / fact / label），含 `registration_status` 治理字段、`lineage_constraint_failure`、类型特定校验。
- `DataFreshness`: 条件必填规则（hard-capable export 存在时）。
- `domain_status` ↔ `stance` 硬约束映射（SPEC-004 §8.3）。
- `confidence` dual cap（data_quality + domain_status）。
- `completed + unavailable` 禁止组合（§5.3）。
- Extra fields forbidden（严格落实）。
- 生成的 JSON Schema。

## Run

```powershell
cd executable_specs/spec004
python -m pytest
python scripts/export_schema.py
```

## Normative Order

1. Functions in `src/crosslens_spec004/`.
2. Contracts in `src/crosslens_spec004/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-004).

## Source

- [SPEC-004 五类分析能力域与 Analysis Card Schema](../../SPEC-004%20五类分析能力域与%20Analysis%20Card%20Schema%20v0.2.6.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
