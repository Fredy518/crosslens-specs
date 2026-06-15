# SPEC-003 Executable Specification

> 📋 **计划中** — 尚未实现。

## Planned Scope

- Evidence Packet schema: Pydantic v2 契约 + JSON Schema 生成。
- `generation_type` 枚举：computed / structured / interpreted。
- `determinism_level` 枚举：computed / structured / interpreted / low / unknown。
- `can_support_hard_constraint` 级联规则。
- Confidence 赋值规则（继承 SPEC-005 §4.4）。
- Validation Report schema。
- Conflict Report schema。
- Decision Candidate schema。
- Event Log schema。

## Target Normative Order

实现后，规范优先级为：

1. Functions in `src/crosslens_spec003/`.
2. Contracts in `src/crosslens_spec003/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-003).

## Source

- [SPEC-003 Agentic投研工作流架构](../../SPEC-003%20Agentic投研工作流架构%20v0.3.4.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
