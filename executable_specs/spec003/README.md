# SPEC-003 Executable Specification

✅ **已实现** — Evidence Packet, Analysis Domain Job, Validation Report, Conflict Report, Decision Candidate Pydantic v2 契约 + 边界测试 + JSON Schema。

## Scope

- `EvidencePacket`: 16-field Pydantic v2 model — the most consumed data object in the pipeline.
- `AnalysisDomainJob`: Orchestrator → Domain dispatch work order (task_ref + context_ref + evidence_refs + constraints + run_config).
- `PostCardValidationReport`: Post-card quality check results with block/flag/note severity.
- `ConflictReport`: Cross-domain conflict record with has_blocking_conflict flag.
- `DecisionCandidate`: Final decision proposal with output_control support.
- Enums: `GenerationType`, `DeterminismLevel`, `Domain`, `DataQuality`, `DomainStatus`, `Stance`, `ValidationSeverity`, `ConflictSeverity`.
- `DomainStatusReason`: reason_code enum (insufficient_data, skipped_by_config, execution_failure, data_source_unavailable) without splitting the canonical domain_status.
- All domain_status and stance values aligned to Registry.
- Interpreted Evidence → can_support_hard_constraint=false enforced.
- Computed Evidence confidence defaults to 1.0.

## Run

```powershell
cd executable_specs/spec003
python -m pytest
python scripts/export_schema.py
```

## Normative Order

1. Functions in `src/crosslens_spec003/`.
2. Contracts in `src/crosslens_spec003/models.py`.
3. Boundary examples in `tests/`.
4. Generated JSON Schema in `schemas/`.
5. Explanatory Markdown (SPEC-003).

## Source

- [SPEC-003 Agentic投研工作流架构](../../SPEC-003%20Agentic投研工作流架构%20v0.3.4.md)
- [SPEC-REGISTRY](../../SPEC-REGISTRY.md)
