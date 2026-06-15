"""JSON Schema generation for SPEC-009 Governance contracts."""

from .models import (
    EvaluationReport,
    GuardrailReport,
    ResolvedDecisionBounds,
)

__all__ = [
    "guardrail_report_schema",
    "evaluation_report_schema",
    "resolved_decision_bounds_schema",
]


def _json_schema(model_cls):
    return model_cls.model_json_schema()


guardrail_report_schema = _json_schema(GuardrailReport)
evaluation_report_schema = _json_schema(EvaluationReport)
resolved_decision_bounds_schema = _json_schema(ResolvedDecisionBounds)
