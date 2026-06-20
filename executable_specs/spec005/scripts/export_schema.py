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

# Canonical model → schema-file mapping (consumed by tests/test_schema.py).
SPECS = {
    "spec005-metric_registry_entry.schema.json": MetricRegistryEntry,
    "spec005-fact_registry_entry.schema.json": FactRegistryEntry,
    "spec005-label_registry_entry.schema.json": LabelRegistryEntry,
    "spec005-derived_metric_rule_table.schema.json": DerivedMetricRuleTable,
}


def render_schema(model_cls) -> str:
    """Serialize a Pydantic model's JSON Schema in the canonical format.

    Format: indent=2, sort_keys=True, ensure_ascii=False, trailing newline.
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
