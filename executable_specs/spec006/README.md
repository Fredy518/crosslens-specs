# SPEC-006 Executable Specification

This directory is the normative executable definition for the SPEC-006 decision semantics.

## Scope

- `aggregate_multi_rule`: `all` / `any` child-status aggregation.
- `compute_overall_result`: SPEC-006 overall-result decision tree.
- `merge_confidence_cap`: deterministic multi-source confidence-cap merging.
- Pydantic contracts for constraint results and evaluation outputs.
- Boundary tests and generated JSON Schema.

Markdown explains design intent. This package defines executable behavior. Tests define required boundary examples.

## Run

```powershell
python -m pytest
python scripts/export_schema.py
```

Run both commands from this directory. Schema generation is deterministic; a changed generated file must be reviewed with the code change.

## Normative Order

No release is valid unless all boundary tests pass. Within a valid release, precedence is:

1. Functions in `src/crosslens_spec006/decision_logic.py`.
2. Contracts in `src/crosslens_spec006/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown.

This precedence applies only to the executable scope listed above, not to unrelated product or governance policy.
