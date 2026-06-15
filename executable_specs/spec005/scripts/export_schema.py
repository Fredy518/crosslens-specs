"""Generate JSON Schema artifacts for SPEC-005 contracts."""

import json
from pathlib import Path

from crosslens_spec005.models import (
    DerivedMetricRuleTable,
    FactRegistryEntry,
    LabelRegistryEntry,
    MetricRegistryEntry,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMAS_DIR.mkdir(exist_ok=True)

specs = {
    "spec005-metric_registry_entry.schema.json": MetricRegistryEntry,
    "spec005-fact_registry_entry.schema.json": FactRegistryEntry,
    "spec005-label_registry_entry.schema.json": LabelRegistryEntry,
    "spec005-derived_metric_rule_table.schema.json": DerivedMetricRuleTable,
}

for filename, model_cls in specs.items():
    schema = model_cls.model_json_schema()
    path = SCHEMAS_DIR / filename
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] {filename}")
