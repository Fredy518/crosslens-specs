from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConstraintStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"
    STALE_DATA = "stale_data"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class ConstraintType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class ImpactOnDecision(str, Enum):
    SUPPORT = "support"
    NEUTRAL = "neutral"
    CAUTION = "caution"
    LOWER_CONFIDENCE = "lower_confidence"
    BLOCK_STRONG_BUY = "block_strong_buy"
    BLOCK_STRONG_SELL = "block_strong_sell"
    BLOCK_NEW_POSITION = "block_new_position"
    BLOCK_ADD_POSITION = "block_add_position"
    REQUIRE_HUMAN_REVIEW = "require_human_review"
    NEED_MORE_DATA = "need_more_data"


class OverallResult(str, Enum):
    PASSED = "passed"
    PASSED_WITH_CAUTION = "passed_with_caution"
    PARTIALLY_PASSED = "partially_passed"
    NOT_PASSED_FOR_NEW_BUY = "not_passed_for_new_buy"
    NOT_PASSED_FOR_ADD_POSITION = "not_passed_for_add_position"
    NOT_SUITABLE_FOR_PLAYBOOK = "not_suitable_for_playbook"
    NEED_MORE_DATA = "need_more_data"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class AllowedAction(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    WAIT = "wait"
    AVOID = "avoid"
    REDUCE = "reduce"
    ADD_TO_WATCHLIST = "add_to_watchlist"
    HOLD_IF_ALREADY_OWNED = "hold_if_already_owned"
    NEED_MORE_DATA = "need_more_data"
    ADD_POSITION = "add_position"


class ApplicabilityStatus(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    UNKNOWN = "unknown"


class ReviewSignal(str, Enum):
    AMBIGUOUS_LABEL_REF = "ambiguous_label_ref"
    CONFLICT_HANDLING = "conflict_handling"
    HUMAN_REVIEW_POLICY = "human_review_policy"
    VALIDATION = "validation"


class AdjustmentSource(str, Enum):
    PLAYBOOK = "playbook"
    CONFLICT = "conflict"
    VALIDATION = "validation"
    GUARDRAIL = "guardrail"


class ConstraintEvaluationResult(StrictModel):
    constraint_id: str = Field(min_length=1)
    constraint_type: ConstraintType
    status: ConstraintStatus
    impact_on_decision: ImpactOnDecision

    @model_validator(mode="after")
    def validate_mvp_hard_failure(self) -> "ConstraintEvaluationResult":
        valid_hard_fail_impacts = {
            ImpactOnDecision.BLOCK_NEW_POSITION,
            ImpactOnDecision.BLOCK_ADD_POSITION,
            ImpactOnDecision.REQUIRE_HUMAN_REVIEW,
        }
        if (
            self.constraint_type is ConstraintType.HARD
            and self.status is ConstraintStatus.FAIL
            and self.impact_on_decision not in valid_hard_fail_impacts
        ):
            raise ValueError(
                "MVP hard fail must block a position action or require human review"
            )
        return self

    @model_validator(mode="after")
    def validate_soft_impact(self) -> "ConstraintEvaluationResult":
        soft_disallowed_impacts = {
            ImpactOnDecision.BLOCK_NEW_POSITION,
            ImpactOnDecision.BLOCK_ADD_POSITION,
            ImpactOnDecision.NEED_MORE_DATA,
        }
        if (
            self.constraint_type is ConstraintType.SOFT
            and self.impact_on_decision in soft_disallowed_impacts
        ):
            raise ValueError(
                "Soft Constraint must not directly block position actions "
                "or assert need_more_data; use lower_confidence, caution, "
                "or require_human_review instead"
            )
        return self


class OverallResultComputation(StrictModel):
    overall_result: OverallResult
    requires_human_review: bool
    soft_fail_count_total: int = Field(ge=0)
    hard_pass_count: int = Field(ge=0)
    all_hard_not_applicable: bool
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_review_result(self) -> "OverallResultComputation":
        expected = self.overall_result is OverallResult.REQUIRES_HUMAN_REVIEW
        if self.requires_human_review is not expected:
            raise ValueError(
                "Playbook-level requires_human_review must match overall_result"
            )
        return self


class PlaybookEvaluationReport(StrictModel):
    overall_result: OverallResult
    requires_human_review: bool
    soft_fail_count_total: int = Field(ge=0)
    constraint_results: tuple[ConstraintEvaluationResult, ...]
    recommended_decision_bounds: tuple[AllowedAction, ...]
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_derived_fields(self) -> "PlaybookEvaluationReport":
        actual_soft_fail_count = sum(
            result.constraint_type is ConstraintType.SOFT
            and result.status is ConstraintStatus.FAIL
            for result in self.constraint_results
        )
        if self.soft_fail_count_total != actual_soft_fail_count:
            raise ValueError("soft_fail_count_total does not match constraint_results")

        expected_review = self.overall_result is OverallResult.REQUIRES_HUMAN_REVIEW
        if self.requires_human_review is not expected_review:
            raise ValueError(
                "Playbook-level requires_human_review must match overall_result"
            )
        return self


class ConfidenceAdjustment(StrictModel):
    source: AdjustmentSource
    source_ref: str = Field(min_length=1)
    amount: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))


class ConfidenceCapStep(StrictModel):
    source: AdjustmentSource
    source_ref: str
    cap_before: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    adjustment: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    cap_after: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))


class ConfidenceCapResult(StrictModel):
    initial_cap: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    final_cap: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    review_threshold: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    requires_human_review: bool
    steps: tuple[ConfidenceCapStep, ...]
