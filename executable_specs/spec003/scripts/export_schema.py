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

# Canonical model → schema-file mapping (consumed by tests/test_schema.py).
SPECS = {
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


def render_schema(model_cls) -> str:
    """Serialize a Pydantic model's JSON Schema in the canonical format.

    Format: indent=2, sort_keys=True, ensure_ascii=False, trailing newline.
    Mirrors spec006's render_contract_schema so all packages stay consistent.
    """
    schema = model_cls.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    SCHEMAS_DIR.mkdir(exist_ok=True)
    for filename, model_cls in SPECS.items():
        path = SCHEMAS_DIR / filename
        path.write_text(render_schema(model_cls), encoding="utf-8")
        print(f"[OK] {filename}")


if __name__ == "__main__":
    main()
