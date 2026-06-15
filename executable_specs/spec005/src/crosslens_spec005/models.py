"""Pydantic v2 contracts for SPEC-005 Metric Registry schema."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Determination Type ─────────────────────────────────────────

class DeterminationType(str, Enum):
    COMPUTED_DEFAULT = "computed_default"
    COMPUTED_WITH_EVENT_LINEAGE_CHECK = "computed_with_event_lineage_check"
    MODEL_OUTPUT = "model_output"
    DERIVED_RULE = "derived_rule"
    LLM_INTERPRETED = "llm_interpreted"


# ── Value Type ─────────────────────────────────────────────────

class ValueType(str, Enum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    STRING = "string"


# ── Metric Category ────────────────────────────────────────────

class MetricCategory(str, Enum):
    COMPUTED = "computed"
    STRUCTURED = "structured"
    INTERPRETED = "interpreted"
    DERIVED = "derived"


# ── Metric Registry Entry ──────────────────────────────────────

class FreshnessRequirement(StrictModel):
    update_frequency: str = ""
    staleness_threshold_days: int = Field(ge=0)
    valid_until_rule: str = ""
    description: str = ""


class ConfidenceMetadata(StrictModel):
    determination_type: DeterminationType
    default_confidence: float | None = None
    confidence_cap_reason: str = ""
    confidence_downgrade_factors: list[str] = []
    model_id: str | None = None
    model_version: str | None = None
    confidence_source: str | None = None
    description: str = ""


class LineageConstraints(StrictModel):
    requires_source_event_ref: bool = False
    source_event_certainty_must_be: str | None = None
    source_event_generation_type_must_not_be: str | None = None
    description: str = ""


class ComputationConstraints(StrictModel):
    must_not_infer_from_macro_label: str | None = None
    required_inputs: list[str] = []
    description: str = ""


class MetricRegistryEntry(StrictModel):
    metric_id: str = Field(min_length=1)
    display_name: str = ""
    description: str = ""
    value_type: ValueType
    unit: str = ""
    metric_category: MetricCategory
    source_domain: str = Field(min_length=1)
    producing_package: str = ""
    producing_capability: str = ""
    evidence_type: str = ""
    generation_type: str = ""
    determinism_level: str = ""  # computed | structured | interpreted
    can_support_hard_constraint: bool
    evidence_value_path: str = ""
    expected_export_ref: str = Field(min_length=1)
    freshness_requirement: FreshnessRequirement | None = None
    confidence_metadata: ConfidenceMetadata
    lineage_constraints: LineageConstraints | None = None
    computation_constraints: ComputationConstraints | None = None
    related_metrics: list[str] = []
    tags: list[str] = []

    @model_validator(mode="after")
    def _expected_export_ref_matches_metric_id(self) -> "MetricRegistryEntry":
        """expected_export_ref must be metric://<metric_id>"""
        expected = f"metric://{self.metric_id}"
        if self.expected_export_ref != expected:
            raise ValueError(
                f"expected_export_ref={self.expected_export_ref} "
                f"must equal metric://{self.metric_id}"
            )
        return self

    @model_validator(mode="after")
    def _confidence_matches_determination(self) -> "MetricRegistryEntry":
        """default_confidence rules per determination_type (§4.4.5)."""
        dt = self.confidence_metadata.determination_type
        if dt is DeterminationType.COMPUTED_DEFAULT:
            if self.confidence_metadata.default_confidence != 1.0:
                raise ValueError(
                    "computed_default must have default_confidence = 1.0"
                )
        elif dt is DeterminationType.MODEL_OUTPUT:
            if self.confidence_metadata.model_id is None:
                raise ValueError(
                    "model_output requires model_id in confidence_metadata"
                )
        elif dt is DeterminationType.LLM_INTERPRETED:
            if self.can_support_hard_constraint:
                raise ValueError(
                    "llm_interpreted must not have can_support_hard_constraint=true"
                )
        return self


# ── Fact Registry Entry ────────────────────────────────────────

class FactRegistryEntry(StrictModel):
    fact_id: str = Field(min_length=1)
    display_name: str = ""
    description: str = ""
    value_type: ValueType
    source_domain: str = Field(min_length=1)
    producing_package: str = ""
    can_support_hard_constraint: bool
    expected_export_ref: str = Field(min_length=1)
    production_contract: str = ""

    @model_validator(mode="after")
    def _expected_ref_matches_fact_id(self) -> "FactRegistryEntry":
        expected = f"fact://{self.fact_id}"
        if self.expected_export_ref != expected:
            raise ValueError(
                f"expected_export_ref={self.expected_export_ref} "
                f"must equal fact://{self.fact_id}"
            )
        return self


# ── Label Registry Entry ───────────────────────────────────────

class LabelRegistryEntry(StrictModel):
    label_id: str = Field(min_length=1)
    display_name: str = ""
    allowed_values: list[str] = Field(min_length=1)
    source_domain: str = Field(min_length=1)
    producing_package: str = ""
    can_support_hard_constraint: bool
    expected_export_ref: str = Field(min_length=1)
    derivation_rule: str = ""

    @model_validator(mode="after")
    def _expected_ref_matches_label_id(self) -> "LabelRegistryEntry":
        expected = f"label://{self.label_id}"
        if self.expected_export_ref != expected:
            raise ValueError(
                f"expected_export_ref={self.expected_export_ref} "
                f"must equal label://{self.label_id}"
            )
        return self


# ── Derived Metric Rule Table ──────────────────────────────────

class ConfidenceRule(str, Enum):
    INHERIT_MIN = "inherit_min"


class RuleOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"


class DerivedRuleCondition(StrictModel):
    input_ref: str = Field(min_length=1)
    operator: RuleOperator
    value: float | list[float]  # scalar for most ops, [lower, upper) for between


class DerivedRuleOutput(StrictModel):
    fact_value: bool
    label: str = Field(min_length=1)


class DerivedRule(StrictModel):
    rule_id: str = Field(min_length=1)
    condition: DerivedRuleCondition
    output: DerivedRuleOutput
    description: str = ""


class DerivedRuleTestCase(StrictModel):
    input: dict[str, float | None]
    expected_output: DerivedRuleOutput


class DerivedMetricRuleTable(StrictModel):
    rule_table_id: str = Field(min_length=1)
    derived_metric_id: str = Field(min_length=1)
    description: str = ""
    spec_version: str = ""
    rules: list[DerivedRule] = Field(min_length=1)
    default_output: DerivedRuleOutput
    determinism_level: str = "computed"
    confidence_rule: ConfidenceRule = ConfidenceRule.INHERIT_MIN
    test_cases: list[DerivedRuleTestCase] = Field(min_length=1)

    @model_validator(mode="after")
    def _every_rule_id_has_test(self) -> "DerivedMetricRuleTable":
        """Each rule_id must be covered by at least one test_case."""
        rule_ids = {r.rule_id for r in self.rules}
        tested_ids = set()
        for tc in self.test_cases:
            mapped = self._apply_rule_table(dict(tc.input))
            if mapped is not None:
                tested_ids.add(mapped[0])
        uncovered = rule_ids - tested_ids
        if uncovered:
            raise ValueError(
                f"test_cases must cover all rule_ids; missing: {uncovered}"
            )
        return self

    def _apply_rule_table(
        self, inputs: dict[str, float | None]
    ) -> tuple[str, DerivedRuleOutput] | None:
        """First-match-short-circuit over rules in order."""
        for rule in self.rules:
            cond = rule.condition
            raw = inputs.get(cond.input_ref)
            if raw is None:
                continue
            if not isinstance(raw, (int, float)):
                continue
            op = cond.operator
            if op is RuleOperator.EQ and raw == cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.NEQ and raw != cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.GT and raw > cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.GTE and raw >= cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.LT and raw < cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.LTE and raw <= cond.value:
                return (rule.rule_id, rule.output)
            if op is RuleOperator.BETWEEN:
                lower, upper = cond.value if isinstance(cond.value, list) else (0, 0)
                if lower <= raw < upper:
                    return (rule.rule_id, rule.output)
        return None
