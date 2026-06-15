"""JSON Schema generation for SPEC-004 Analysis Card contracts."""

from .models import (
    AnalysisCard,
    ConstraintExport,
    DataFreshness,
    EvidenceCoverage,
    EvidenceRef,
)

__all__ = [
    "analysis_card_schema",
    "constraint_export_schema",
    "data_freshness_schema",
    "evidence_coverage_schema",
    "evidence_ref_schema",
]


def _json_schema(model_cls):
    return model_cls.model_json_schema()


analysis_card_schema = _json_schema(AnalysisCard)
constraint_export_schema = _json_schema(ConstraintExport)
data_freshness_schema = _json_schema(DataFreshness)
evidence_coverage_schema = _json_schema(EvidenceCoverage)
evidence_ref_schema = _json_schema(EvidenceRef)
