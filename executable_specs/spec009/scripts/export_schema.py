"""Generate JSON Schema artifacts for SPEC-009 contracts."""

import json
from pathlib import Path

from crosslens_spec009.models import (
    EvaluationReport,
    GuardrailReport,
    ResolvedDecisionBounds,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMAS_DIR.mkdir(exist_ok=True)

specs = {
    "spec009-guardrail_report.schema.json": GuardrailReport,
    "spec009-evaluation_report.schema.json": EvaluationReport,
    "spec009-resolved_decision_bounds.schema.json": ResolvedDecisionBounds,
}

for filename, model_cls in specs.items():
    schema = model_cls.model_json_schema()
    path = SCHEMAS_DIR / filename
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] {filename}")
