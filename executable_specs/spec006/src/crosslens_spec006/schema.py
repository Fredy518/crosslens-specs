from __future__ import annotations

import json
from typing import Any

from .models import (
    ConfidenceCapResult,
    ConstraintEvaluationResult,
    OverallResultComputation,
    PlaybookEvaluationReport,
)


def build_contract_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "crosslens SPEC-006 executable contracts",
        "models": {
            "ConstraintEvaluationResult": ConstraintEvaluationResult.model_json_schema(),
            "OverallResultComputation": OverallResultComputation.model_json_schema(),
            "PlaybookEvaluationReport": PlaybookEvaluationReport.model_json_schema(),
            "ConfidenceCapResult": ConfidenceCapResult.model_json_schema(),
        },
    }


def render_contract_schema() -> str:
    return (
        json.dumps(
            build_contract_schema(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
