from pathlib import Path

from crosslens_spec006.schema import render_contract_schema


ROOT = Path(__file__).resolve().parents[1]


def test_generated_schema_is_current():
    schema_path = ROOT / "schemas" / "spec006-contracts.schema.json"

    assert schema_path.read_text(encoding="utf-8") == render_contract_schema()
