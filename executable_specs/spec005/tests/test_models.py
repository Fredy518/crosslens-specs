"""Tests for SPEC-005 Metric Registry Pydantic contracts."""

import pytest

from crosslens_spec005.models import (
    ConfidenceMetadata,
    ConfidenceRule,
    DerivedMetricRuleTable,
    DerivedRule,
    DerivedRuleCondition,
    DerivedRuleOutput,
    DerivedRuleTestCase,
    DeterminationType,
    FactRegistryEntry,
    FreshnessRequirement,
    LabelRegistryEntry,
    MetricCategory,
    MetricRegistryEntry,
    RuleOperator,
    ValueType,
)


# ── Helpers ────────────────────────────────────────────────────

def _valid_metric_entry(**overrides) -> dict:
    base = {
        "metric_id": "revenue_growth_ttm",
        "display_name": "TTM 收入增速",
        "description": "过去四个季度的总收入同比增长率",
        "value_type": ValueType.NUMBER,
        "unit": "percent",
        "metric_category": MetricCategory.COMPUTED,
        "source_domain": "fundamentals",
        "producing_package": "pkg_fundamentals_financial_v1",
        "producing_capability": "cap_financial_metric_compute",
        "evidence_type": "financial_metrics",
        "generation_type": "computed",
        "determinism_level": "computed",
        "can_support_hard_constraint": True,
        "evidence_value_path": "revenue_growth_ttm",
        "expected_export_ref": "metric://revenue_growth_ttm",
        "freshness_requirement": {
            "update_frequency": "quarterly",
            "staleness_threshold_days": 120,
            "valid_until_rule": "next_quarter_end_plus_45_days",
            "description": "每季度有效",
        },
        "confidence_metadata": {
            "determination_type": DeterminationType.COMPUTED_DEFAULT,
            "default_confidence": 1.0,
            "confidence_cap_reason": "确定性计算",
        },
        "tags": ["growth", "revenue"],
    }
    base.update(overrides)
    return base


# ── Valid Entries ──────────────────────────────────────────────

def test_valid_metric_entry():
    entry = MetricRegistryEntry.model_validate(_valid_metric_entry())
    assert entry.metric_id == "revenue_growth_ttm"
    assert entry.can_support_hard_constraint is True


def test_valid_fact_entry():
    entry = FactRegistryEntry(
        fact_id="retail_sentiment_overheated",
        display_name="散户情绪过热",
        description="散户渠道情绪处于过热区域",
        value_type=ValueType.BOOLEAN,
        source_domain="sentiment",
        producing_package="pkg_sentiment_social_v1",
        can_support_hard_constraint=False,
        expected_export_ref="fact://retail_sentiment_overheated",
    )
    assert entry.fact_id == "retail_sentiment_overheated"


def test_valid_label_entry():
    entry = LabelRegistryEntry(
        label_id="industry_cycle_stage",
        display_name="行业周期阶段",
        allowed_values=["early_recovery", "expansion", "peak", "contraction"],
        source_domain="macro_meso",
        producing_package="pkg_industry_cycle_classifier_v1",
        can_support_hard_constraint=False,
        expected_export_ref="label://industry_cycle_stage",
    )
    assert entry.label_id == "industry_cycle_stage"


# ── Expected Export Ref ────────────────────────────────────────

def test_metric_export_ref_must_match():
    with pytest.raises(ValueError, match="expected_export_ref"):
        MetricRegistryEntry.model_validate(
            _valid_metric_entry(
                expected_export_ref="metric://wrong_metric_id"
            )
        )


def test_fact_export_ref_must_match():
    with pytest.raises(ValueError, match="expected_export_ref"):
        FactRegistryEntry(
            fact_id="test_fact",
            value_type=ValueType.BOOLEAN,
            source_domain="fundamentals",
            producing_package="pkg_v1",
            can_support_hard_constraint=False,
            expected_export_ref="fact://different_fact",
        )


def test_label_export_ref_must_match():
    with pytest.raises(ValueError, match="expected_export_ref"):
        LabelRegistryEntry(
            label_id="test_label",
            allowed_values=["a", "b"],
            source_domain="fundamentals",
            producing_package="pkg_v1",
            can_support_hard_constraint=False,
            expected_export_ref="label://wrong_label",
        )


# ── Confidence Determination Rules ─────────────────────────────

def test_computed_default_confidence_must_be_1():
    with pytest.raises(ValueError, match="default_confidence.*1.0"):
        MetricRegistryEntry.model_validate(
            _valid_metric_entry(
                confidence_metadata={
                    "determination_type": DeterminationType.COMPUTED_DEFAULT,
                    "default_confidence": 0.8,
                }
            )
        )


def test_model_output_requires_model_id():
    with pytest.raises(ValueError, match="model_id"):
        MetricRegistryEntry.model_validate(
            _valid_metric_entry(
                metric_id="bullish_ratio",
                expected_export_ref="metric://bullish_ratio",
                metric_category=MetricCategory.STRUCTURED,
                determinism_level="structured",
                can_support_hard_constraint=False,
                confidence_metadata={
                    "determination_type": DeterminationType.MODEL_OUTPUT,
                    "default_confidence": None,
                },
            )
        )


def test_llm_interpreted_cannot_support_hard():
    with pytest.raises(ValueError, match="llm_interpreted.*hard_constraint"):
        MetricRegistryEntry.model_validate(
            _valid_metric_entry(
                metric_category=MetricCategory.INTERPRETED,
                determinism_level="interpreted",
                can_support_hard_constraint=True,
                confidence_metadata={
                    "determination_type": DeterminationType.LLM_INTERPRETED,
                    "default_confidence": None,
                },
            )
        )


# ── Derived Metric Rule Table ──────────────────────────────────

_VALID_RULE_TABLE = {
    "rule_table_id": "rule_valuation_state_v1",
    "derived_metric_id": "valuation_state",
    "description": "PE 分位数 → 估值状态",
    "spec_version": "SPEC-005@0.2",
    "rules": [
        {
            "rule_id": "r001",
            "condition": {
                "input_ref": "metric://pe_percentile_5y",
                "operator": RuleOperator.GTE,
                "value": 0.80,
            },
            "output": {"fact_value": True, "label": "expensive"},
            "description": "PE分位 >= 80% → expensive",
        },
        {
            "rule_id": "r002",
            "condition": {
                "input_ref": "metric://pe_percentile_5y",
                "operator": RuleOperator.BETWEEN,
                "value": [0.30, 0.80],
            },
            "output": {"fact_value": True, "label": "fair"},
            "description": "30% ≤ PE < 80% → fair",
        },
        {
            "rule_id": "r003",
            "condition": {
                "input_ref": "metric://pe_percentile_5y",
                "operator": RuleOperator.LT,
                "value": 0.30,
            },
            "output": {"fact_value": True, "label": "cheap"},
            "description": "PE分位 < 30% → cheap",
        },
    ],
    "default_output": {"fact_value": False, "label": "unavailable"},
    "confidence_rule": ConfidenceRule.INHERIT_MIN,
    "test_cases": [
        {
            "input": {"metric://pe_percentile_5y": 0.85},
            "expected_output": {"fact_value": True, "label": "expensive"},
        },
        {
            "input": {"metric://pe_percentile_5y": 0.50},
            "expected_output": {"fact_value": True, "label": "fair"},
        },
        {
            "input": {"metric://pe_percentile_5y": 0.15},
            "expected_output": {"fact_value": True, "label": "cheap"},
        },
        {
            "input": {"metric://pe_percentile_5y": None},
            "expected_output": {"fact_value": False, "label": "unavailable"},
        },
    ],
}


def test_valid_rule_table():
    rt = DerivedMetricRuleTable.model_validate(_VALID_RULE_TABLE)
    assert rt.rules[0].rule_id == "r001"
    assert rt.confidence_rule == ConfidenceRule.INHERIT_MIN


def test_rule_table_must_cover_all_rules_with_tests():
    bad = dict(_VALID_RULE_TABLE)
    bad["rules"] = bad["rules"].copy() + [
        {
            "rule_id": "r004",
            "condition": {
                "input_ref": "metric://pe_percentile_5y",
                "operator": RuleOperator.EQ,
                "value": 0.99,
            },
            "output": {"fact_value": True, "label": "extreme"},
            "description": "PE=0.99 → extreme",
        }
    ]
    with pytest.raises(ValueError, match="test_cases.*cover.*r004"):
        DerivedMetricRuleTable.model_validate(bad)


def test_rule_table_first_match_short_circuit():
    rt = DerivedMetricRuleTable.model_validate(_VALID_RULE_TABLE)
    result = rt._apply_rule_table({"metric://pe_percentile_5y": 0.85})
    assert result is not None
    assert result[1].label == "expensive"


def test_rule_table_null_input_returns_none():
    rt = DerivedMetricRuleTable.model_validate(_VALID_RULE_TABLE)
    result = rt._apply_rule_table({"metric://pe_percentile_5y": None})
    assert result is None


# ── Extra Fields Forbidden ─────────────────────────────────────

def test_metric_entry_extra_forbidden():
    with pytest.raises(ValueError, match="extra.*forbid|Extra inputs"):
        MetricRegistryEntry.model_validate(_valid_metric_entry(unknown=True))
