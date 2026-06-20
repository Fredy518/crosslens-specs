"""Schema freshness — checked-in JSON Schema must match model_json_schema().

Guards against silent drift between the Python models and the checked-in
schemas/*.schema.json artifacts. Mirrors spec006's test_schema.py.
"""

from pathlib import Path

import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "export_schema.py"

# Load export_schema.py as a module (it lives outside the package).
_spec = importlib.util.spec_from_file_location("export_schema", SCRIPTS)
export_schema = importlib.util.module_from_spec(_spec)
sys.modules["export_schema"] = export_schema
_spec.loader.exec_module(export_schema)


def test_checked_in_schemas_match_models():
    missing_files: list[str] = []
    mismatches: list[str] = []
    for filename, model_cls in export_schema.SPECS.items():
        path = ROOT / "schemas" / filename
        if not path.exists():
            missing_files.append(filename)
            continue
        if path.read_text(encoding="utf-8") != export_schema.render_schema(model_cls):
            mismatches.append(filename)
    assert not missing_files, f"missing schema files: {missing_files}"
    assert not mismatches, (
        f"schema files out of date with models (run scripts/export_schema.py): "
        f"{mismatches}"
    )
