from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "schemas" / "spec006-contracts.schema.json"
sys.path.insert(0, str(ROOT / "src"))

from crosslens_spec006.schema import render_contract_schema  # noqa: E402


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_contract_schema(), encoding="utf-8")


if __name__ == "__main__":
    main()
