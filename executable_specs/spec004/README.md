# SPEC-004 Executable Specification

> 📋 **计划中** — 尚未实现。

## Planned Scope

- Analysis Card schema: Pydantic v2 契约 + JSON Schema 生成。
- `domain_status` 枚举：规范性校验。
- `stance` 枚举：规范性校验。
- `constraint_exports` 契约：接口定义与边界测试。
- Post-card Validation (8 项 schema 检查) 可执行版本。

## Target Normative Order

实现后，规范优先级为：

1. Functions in `src/crosslens_spec004/`.
2. Contracts in `src/crosslens_spec004/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-004).

## Source

- [SPEC-004 五类分析能力域与 Analysis Card Schema](../../SPEC-004%20五类分析能力域与%20Analysis%20Card%20Schema%20v0.2.5.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
