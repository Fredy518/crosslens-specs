"""Generate JSON Schema artifacts for SPEC-004 contracts."""

import json
from pathlib import Path

from crosslens_spec004.models import AnalysisCard, ConstraintExport, DataFreshness

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMAS_DIR.mkdir(exist_ok=True)

specs = {
    "spec004-analysis_card.schema.json": AnalysisCard,
    "spec004-constraint_export.schema.json": ConstraintExport,
    "spec004-data_freshness.schema.json": DataFreshness,
}

for filename, model_cls in specs.items():
    schema = model_cls.model_json_schema()
    path = SCHEMAS_DIR / filename
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] {filename}")
