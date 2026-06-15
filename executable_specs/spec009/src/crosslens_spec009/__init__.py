"""
crosslens_spec009 — Executable governance contracts for SPEC-009.

Normative definitions for:
- GuardrailReport (6 rules + findings + blocked_candidate_actions + output_control)
- EvaluationReport (4 dimensions + quality_flags + confidence_cap_adjustments)
- ResolvedDecisionBounds (allowed_actions + requires_human_review + confidence_cap)
- apply_guardrails — guardrail decision tree with narrow_bounds
- run_evaluator — four-dimension quality check
- compute_final_confidence_cap — three-layer cap merge (Guardrail > Evaluator > Preference)
- aggregate_human_review_signals — six-source signal aggregation
- resolve_decision_bounds — complete merge algorithm
- check_evidence_contamination — recursive lineage contamination detection
"""
