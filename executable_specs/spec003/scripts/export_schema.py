"""Generate JSON Schema artifacts for SPEC-003 contracts."""

import json
from pathlib import Path

from crosslens_spec003.models import (
    AnalysisDomainJob,
    AssetInfo,
    ConflictReport,
    ContextBundle,
    ContextSource,
    DecisionCandidate,
    EvidencePacket,
    InvestmentTask,
    PostCardValidationReport,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMAS_DIR.mkdir(exist_ok=True)

specs = {
    "spec003-evidence_packet.schema.json": EvidencePacket,
    "spec003-context_bundle.schema.json": ContextBundle,
    "spec003-context_source.schema.json": ContextSource,
    "spec003-investment_task.schema.json": InvestmentTask,
    "spec003-asset_info.schema.json": AssetInfo,
    "spec003-analysis_domain_job.schema.json": AnalysisDomainJob,
    "spec003-post_card_validation_report.schema.json": PostCardValidationReport,
    "spec003-conflict_report.schema.json": ConflictReport,
    "spec003-decision_candidate.schema.json": DecisionCandidate,
}

for filename, model_cls in specs.items():
    schema = model_cls.model_json_schema()
    path = SCHEMAS_DIR / filename
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] {filename}")
