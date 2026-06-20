"""Tests for SPEC-004 Analysis Card Pydantic contracts."""

from datetime import date, datetime

import pytest

from crosslens_spec004.models import (
    AnalysisCard,
    ConstraintExport,
    DataFreshness,
    DataQuality,
    DeterminismLevel,
    Domain,
    DomainStatus,
    DomainStatusReason,
    EvidenceCoverage,
    EvidenceRef,
    ExportType,
    FreshnessLevel,
    RegistrationStatus,
    StalenessRisk,
    Stance,
    TimeHorizonBucket,
)


# ── Helpers ────────────────────────────────────────────────────

def _valid_card(**overrides) -> dict:
    base = {
        "card_id": "card_fundamentals_001",
        "schema_version": "SPEC-004@0.2.7",
        "task_id": "task_001",
        "run_id": "run_001",
        "domain": Domain.FUNDAMENTALS,
        "domain_status": DomainStatus.COMPLETED,
        "summary": "基本面偏正面，但估值安全边际不足。",
        "stance": Stance.MODERATELY_POSITIVE,
        "confidence": 0.66,
        "confidence_reason": ["财务数据完整且来自 Computed Evidence"],
        "time_horizon": "6-12 months",
        "time_horizon_bucket": TimeHorizonBucket.MEDIUM_TERM,
        "time_horizon_days_min": 180,
        "time_horizon_days_max": 365,
        "data_quality": DataQuality.MEDIUM,
        "data_freshness": {
            "as_of": "2026-06-14",
            "oldest_evidence_as_of": "2026-03-31",
            "newest_evidence_as_of": "2026-06-14",
            "freshness_level": FreshnessLevel.QUARTERLY,
            "staleness_risk": StalenessRisk.MEDIUM,
            "valid_until": "2026-07-31",
        },
        "evidence_coverage": {
            "supporting_evidence_count": 3,
            "opposing_evidence_count": 2,
            "missing_required_evidence": [],
        },
        "supporting_evidence": [
            {
                "evidence_id": "ev_financial_001",
                "evidence_type": "financial_metrics",
                "description": "收入增速高于行业中位数。",
                "determinism_level": DeterminismLevel.COMPUTED,
            }
        ],
        "opposing_evidence": [
            {
                "evidence_id": "ev_valuation_001",
                "evidence_type": "valuation_metrics",
                "description": "估值位于过去五年较高分位。",
                "determinism_level": DeterminismLevel.COMPUTED,
            }
        ],
        "key_findings": ["收入增长仍强于行业"],
        "key_risks": ["估值压缩风险"],
        "invalidating_conditions": ["下季度收入增速低于行业中位数"],
        "constraint_exports": [
            {
                "export_type": ExportType.METRIC,
                "export_ref": "metric://revenue_growth_ttm",
                "evidence_ref": "ev_financial_001",
                "value_path": "revenue_growth_ttm",
                "determinism_level": DeterminismLevel.COMPUTED,
                "can_support_hard_constraint": True,
                "allowed_constraint_types": ["hard", "soft"],
            }
        ],
        "domain_payload": {},
        "warnings": [],
        "limitations": [],
        "created_at": "2026-06-14T10:30:00Z",
    }
    base.update(overrides)
    return base


# ── Valid Card ─────────────────────────────────────────────────

def test_valid_analysis_card():
    card = AnalysisCard.model_validate(_valid_card())
    assert card.card_id == "card_fundamentals_001"
    assert card.domain == Domain.FUNDAMENTALS


def test_minimal_card_partial_without_exports():
    card = AnalysisCard.model_validate(
        _valid_card(
            domain_status=DomainStatus.PARTIAL,
            stance=Stance.UNAVAILABLE,
            confidence=0.40,
            constraint_exports=[],
            data_freshness=None,
            supporting_evidence=[],
            opposing_evidence=[],
        )
    )
    assert card.domain_status == DomainStatus.PARTIAL


# ── Forbidden Combinations ─────────────────────────────────────

def test_completed_unavailable_forbidden():
    with pytest.raises(ValueError, match="completed.*unavailable.*forbidden"):
        AnalysisCard.model_validate(
            _valid_card(data_quality=DataQuality.UNAVAILABLE)
        )


def test_completed_requires_evidence():
    with pytest.raises(ValueError, match="supporting_evidence or opposing_evidence"):
        AnalysisCard.model_validate(
            _valid_card(
                supporting_evidence=[],
                opposing_evidence=[],
            )
        )


# ── Stance Constraints ─────────────────────────────────────────

def test_directional_stance_requires_opposing():
    for stance in [
        Stance.POSITIVE, Stance.MODERATELY_POSITIVE, Stance.MIXED,
        Stance.NEGATIVE, Stance.MODERATELY_NEGATIVE,
    ]:
        with pytest.raises(ValueError, match="opposing_evidence"):
            AnalysisCard.model_validate(
                _valid_card(stance=stance, opposing_evidence=[])
            )


def test_unavailable_stance_only_for_unavailable_or_partial():
    # unavailable stance with completed → should fail per §8.3
    with pytest.raises(ValueError, match="illegal"):
        AnalysisCard.model_validate(
            _valid_card(
                domain_status=DomainStatus.COMPLETED,
                stance=Stance.UNAVAILABLE,
            )
        )


def test_error_must_be_not_applicable():
    # error with directional stance → illegal
    with pytest.raises(ValueError, match="illegal"):
        AnalysisCard.model_validate(
            _valid_card(
                domain_status=DomainStatus.ERROR,
                stance=Stance.POSITIVE,
                confidence=0.0,
                data_freshness=None,
            )
        )


# ── Confidence Caps ────────────────────────────────────────────

def test_confidence_exceeds_cap_by_quality():
    with pytest.raises(ValueError, match="exceeds cap"):
        AnalysisCard.model_validate(
            _valid_card(data_quality=DataQuality.MEDIUM, confidence=0.75)
        )


def test_confidence_exceeds_cap_by_status():
    with pytest.raises(ValueError, match="exceeds cap"):
        AnalysisCard.model_validate(
            _valid_card(
                domain_status=DomainStatus.PARTIAL,
                stance=Stance.MODERATELY_POSITIVE,
                confidence=0.70,
            )
        )


# ── Data Freshness ─────────────────────────────────────────────

def test_data_freshness_required_with_hard_capable_export():
    with pytest.raises(ValueError, match="data_freshness"):
        AnalysisCard.model_validate(
            _valid_card(data_freshness=None)
        )


def test_data_freshness_omitted_when_no_exports():
    card = AnalysisCard.model_validate(
        _valid_card(
            constraint_exports=[],
            data_freshness=None,
            supporting_evidence=[
                {"evidence_id": "ev_financial_001", "description": "test"}
            ],
        )
    )
    assert card.data_freshness is None


# ── Constraint Export ──────────────────────────────────────────

def test_metric_export_requires_value_path():
    with pytest.raises(ValueError, match="value_path"):
        ConstraintExport(
            export_type=ExportType.METRIC,
            export_ref="metric://test",
            evidence_ref="ev_001",
            determinism_level=DeterminismLevel.COMPUTED,
            can_support_hard_constraint=True,
            allowed_constraint_types=["hard", "soft"],
        )


def test_fact_export_requires_fact_value():
    with pytest.raises(ValueError, match="fact_value"):
        ConstraintExport(
            export_type=ExportType.FACT,
            export_ref="fact://test",
            evidence_ref="ev_001",
            determinism_level=DeterminismLevel.STRUCTURED,
            can_support_hard_constraint=False,
            allowed_constraint_types=["soft"],
        )


def test_label_export_requires_label_value():
    with pytest.raises(ValueError, match="label_value"):
        ConstraintExport(
            export_type=ExportType.LABEL,
            export_ref="label://test",
            evidence_ref="ev_001",
            determinism_level=DeterminismLevel.STRUCTURED,
            can_support_hard_constraint=False,
            allowed_constraint_types=["soft"],
        )


def test_hard_capable_requires_hard_in_allowed_types():
    with pytest.raises(ValueError, match="hard.*allowed_constraint_types"):
        ConstraintExport(
            export_type=ExportType.METRIC,
            export_ref="metric://test",
            evidence_ref="ev_001",
            value_path="test",
            determinism_level=DeterminismLevel.COMPUTED,
            can_support_hard_constraint=True,
            allowed_constraint_types=["soft"],
        )


def test_registration_status_defaults_to_registered():
    export = ConstraintExport(
        export_type=ExportType.METRIC,
        export_ref="metric://revenue_growth_ttm",
        evidence_ref="ev_001",
        value_path="revenue_growth_ttm",
        determinism_level=DeterminismLevel.COMPUTED,
        can_support_hard_constraint=True,
        allowed_constraint_types=["hard", "soft"],
    )
    assert export.registration_status.value == "registered"


def test_unregistered_mvp_local_forbids_hard():
    with pytest.raises(ValueError, match="registration_status=unregistered_mvp_local"):
        ConstraintExport(
            export_type=ExportType.METRIC,
            export_ref="metric://divergence_strength",
            evidence_ref="ev_001",
            value_path="divergence_strength",
            determinism_level=DeterminismLevel.COMPUTED,
            can_support_hard_constraint=True,
            allowed_constraint_types=["hard", "soft"],
            registration_status=RegistrationStatus.UNREGISTERED_MVP_LOCAL,
        )


def test_unregistered_mvp_local_soft_only_ok():
    export = ConstraintExport(
        export_type=ExportType.METRIC,
        export_ref="metric://divergence_strength",
        evidence_ref="ev_001",
        value_path="divergence_strength",
        determinism_level=DeterminismLevel.COMPUTED,
        can_support_hard_constraint=False,
        allowed_constraint_types=["soft"],
        registration_status=RegistrationStatus.UNREGISTERED_MVP_LOCAL,
    )
    assert export.registration_status == RegistrationStatus.UNREGISTERED_MVP_LOCAL


def test_lineage_constraint_failure_optional():
    export = ConstraintExport(
        export_type=ExportType.METRIC,
        export_ref="metric://post_event_1d_return",
        evidence_ref="ev_001",
        value_path="post_event_1d_return",
        determinism_level=DeterminismLevel.COMPUTED,
        can_support_hard_constraint=False,
        allowed_constraint_types=["soft"],
        lineage_constraint_failure="source_event_not_confirmed",
    )
    assert export.lineage_constraint_failure == "source_event_not_confirmed"


# ── Schema Version ─────────────────────────────────────────────

def test_schema_version_format():
    with pytest.raises(ValueError, match="SPEC-004@"):
        AnalysisCard.model_validate(
            _valid_card(schema_version="1.0")
        )


# ── Extra Fields Forbidden ─────────────────────────────────────

def test_extra_fields_forbidden():
    with pytest.raises(ValueError, match="extra.*forbid|Extra inputs"):
        AnalysisCard.model_validate(_valid_card(unknown_field=42))


# ── Data Quality Low Requires Warnings ─────────────────────────

def test_low_quality_requires_warnings():
    with pytest.raises(ValueError, match="data_quality=low.*warning"):
        AnalysisCard.model_validate(
            _valid_card(
                data_quality=DataQuality.LOW,
                confidence=0.30,
                warnings=[],
            )
        )


# ── Domain Status Reason ────────────────────────────────────────

def test_error_requires_domain_status_reason():
    """domain_status=error requires domain_status_reason."""
    with pytest.raises(ValueError, match="domain_status_reason"):
        AnalysisCard.model_validate(
            _valid_card(
                domain_status=DomainStatus.ERROR,
                stance=Stance.NOT_APPLICABLE,
                confidence=0.0,
                constraint_exports=[],
                data_freshness=None,
                supporting_evidence=[],
                opposing_evidence=[],
                domain_status_reason=None,
            )
        )


def test_unavailable_requires_domain_status_reason():
    """domain_status=unavailable requires domain_status_reason."""
    with pytest.raises(ValueError, match="domain_status_reason"):
        AnalysisCard.model_validate(
            _valid_card(
                domain_status=DomainStatus.UNAVAILABLE,
                stance=Stance.UNAVAILABLE,
                confidence=0.0,
                constraint_exports=[],
                data_freshness=None,
                supporting_evidence=[],
                opposing_evidence=[],
                domain_status_reason=None,
            )
        )


def test_completed_with_domain_status_reason_ok():
    """domain_status=completed does not require reason."""
    card = AnalysisCard.model_validate(
        _valid_card(domain_status_reason=None)
    )
    assert card.domain_status_reason is None


# ── Technical/Market domain_payload (v0.2.7 §41 #15–#16) ───────

def _technical_card(**overrides) -> dict:
    base_payload = {
        "key_levels": {
            "support": [],
            "resistance": [],
            "source": "none",
            "note": "P0-P3 empty contract",
            "poc": None,
            "value_area": None,
        },
        "threshold_calibration": {
            "part_i": "uncalibrated",
            "part_ii": None,
        },
    }
    if "domain_payload" in overrides:
        base_payload.update(overrides.pop("domain_payload"))
    return _valid_card(
        domain=Domain.TECHNICAL_MARKET,
        schema_version="SPEC-004@0.2.7",
        constraint_exports=[],
        data_freshness=None,
        domain_payload=base_payload,
        **overrides,
    )


def test_technical_key_levels_empty_p0_contract_ok():
    card = AnalysisCard.model_validate(_technical_card())
    assert card.domain_payload["key_levels"]["support"] == []


def test_technical_key_levels_legacy_number_array_forbidden():
    with pytest.raises(ValueError, match="legacy_key_levels_format"):
        AnalysisCard.model_validate(
            _technical_card(
                domain_payload={
                    "key_levels": {"support": [120, 112], "resistance": []},
                }
            )
        )


def test_technical_key_levels_p4_object_ok():
    card = AnalysisCard.model_validate(
        _technical_card(
            domain_payload={
                "key_levels": {
                    "support": [
                        {
                            "price": 12.30,
                            "strength": 0.72,
                            "source": "volume_poc",
                            "touches": 0,
                        }
                    ],
                    "resistance": [],
                    "source": "support_resistance_metrics",
                    "note": "",
                    "poc": 13.05,
                    "value_area": [12.50, 13.80],
                },
                "threshold_calibration": {
                    "part_i": "uncalibrated",
                    "part_ii": "self_calibrated_percentile",
                },
            }
        )
    )
    assert card.domain_payload["key_levels"]["support"][0]["price"] == 12.30


def test_technical_threshold_calibration_string_forbidden():
    with pytest.raises(ValueError, match="threshold_calibration must be an object"):
        AnalysisCard.model_validate(
            _technical_card(
                domain_payload={"threshold_calibration": "uncalibrated"},
            )
        )
