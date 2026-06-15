"""JSON Schema generation for SPEC-003 core contracts."""

from .models import (
    AnalysisDomainJob,
    ConflictReport,
    DecisionCandidate,
    EvidencePacket,
    PostCardValidationReport,
)

__all__ = [
    "evidence_packet_schema",
    "analysis_domain_job_schema",
    "post_card_validation_report_schema",
    "conflict_report_schema",
    "decision_candidate_schema",
]


def _json_schema(model_cls):
    return model_cls.model_json_schema()


evidence_packet_schema = _json_schema(EvidencePacket)
analysis_domain_job_schema = _json_schema(AnalysisDomainJob)
post_card_validation_report_schema = _json_schema(PostCardValidationReport)
conflict_report_schema = _json_schema(ConflictReport)
decision_candidate_schema = _json_schema(DecisionCandidate)
