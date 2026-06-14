from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from .models import (
    AdjustmentSource,
    AllowedAction,
    ApplicabilityStatus,
    ConfidenceAdjustment,
    ConfidenceCapResult,
    ConfidenceCapStep,
    ConstraintEvaluationResult,
    ConstraintStatus,
    ConstraintType,
    ImpactOnDecision,
    OverallResult,
    OverallResultComputation,
    ReviewSignal,
)


class DecisionLogicError(ValueError):
    pass


def aggregate_multi_rule(
    statuses: Sequence[ConstraintStatus],
    condition_logic: str,
) -> ConstraintStatus:
    applicable = [s for s in statuses if s is not ConstraintStatus.NOT_APPLICABLE]
    if not applicable:
        return ConstraintStatus.NOT_APPLICABLE

    present = set(applicable)
    if condition_logic == "all":
        priority = (
            ConstraintStatus.FAIL,
            ConstraintStatus.ERROR,
            ConstraintStatus.PARTIAL,
            ConstraintStatus.INSUFFICIENT_DATA,
            ConstraintStatus.STALE_DATA,
        )
        return next((status for status in priority if status in present), ConstraintStatus.PASS)

    if condition_logic != "any":
        raise DecisionLogicError(f"unsupported condition_logic: {condition_logic}")

    if ConstraintStatus.PASS in present:
        return ConstraintStatus.PASS
    if ConstraintStatus.ERROR in present:
        return ConstraintStatus.ERROR
    if ConstraintStatus.PARTIAL in present:
        return ConstraintStatus.PARTIAL

    unresolved = {
        ConstraintStatus.INSUFFICIENT_DATA,
        ConstraintStatus.STALE_DATA,
    }
    if ConstraintStatus.FAIL in present and present & unresolved:
        return ConstraintStatus.PARTIAL
    if present == {ConstraintStatus.FAIL}:
        return ConstraintStatus.FAIL
    if ConstraintStatus.INSUFFICIENT_DATA in present:
        return ConstraintStatus.INSUFFICIENT_DATA
    return ConstraintStatus.STALE_DATA


def compute_overall_result(
    constraint_results: Sequence[ConstraintEvaluationResult],
    *,
    review_signals: Iterable[ReviewSignal] = (),
    applicability_status: ApplicabilityStatus = ApplicabilityStatus.APPLICABLE,
    caution_threshold: int = 2,
) -> OverallResultComputation:
    if caution_threshold < 1:
        raise DecisionLogicError("caution_threshold must be at least 1")

    hard = [r for r in constraint_results if r.constraint_type is ConstraintType.HARD]
    soft = [r for r in constraint_results if r.constraint_type is ConstraintType.SOFT]
    soft_fail_count = sum(r.status is ConstraintStatus.FAIL for r in soft)
    hard_pass_count = sum(r.status is ConstraintStatus.PASS for r in hard)
    all_hard_not_applicable = bool(hard) and all(
        r.status is ConstraintStatus.NOT_APPLICABLE for r in hard
    )

    if applicability_status is ApplicabilityStatus.NOT_APPLICABLE:
        return _result(
            OverallResult.NOT_SUITABLE_FOR_PLAYBOOK,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "applicability_not_applicable",
        )

    failed_review_constraint = any(
        r.status is ConstraintStatus.FAIL
        and r.impact_on_decision is ImpactOnDecision.REQUIRE_HUMAN_REVIEW
        for r in constraint_results
    )
    if (
        applicability_status is ApplicabilityStatus.REQUIRES_HUMAN_REVIEW
        or any(review_signals)
        or failed_review_constraint
    ):
        return _result(
            OverallResult.REQUIRES_HUMAN_REVIEW,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "human_review_signal",
        )

    if any(
        r.status is ConstraintStatus.FAIL
        and r.impact_on_decision is ImpactOnDecision.BLOCK_NEW_POSITION
        for r in hard
    ):
        return _result(
            OverallResult.NOT_PASSED_FOR_NEW_BUY,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "hard_fail_block_new_position",
        )

    if any(
        r.status is ConstraintStatus.FAIL
        and r.impact_on_decision is ImpactOnDecision.BLOCK_ADD_POSITION
        for r in hard
    ):
        return _result(
            OverallResult.NOT_PASSED_FOR_ADD_POSITION,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "hard_fail_block_add_position",
        )

    unresolved = {
        ConstraintStatus.PARTIAL,
        ConstraintStatus.INSUFFICIENT_DATA,
        ConstraintStatus.STALE_DATA,
        ConstraintStatus.ERROR,
    }
    if any(r.status in unresolved for r in hard):
        return _result(
            OverallResult.NEED_MORE_DATA,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "hard_constraint_unresolved",
        )

    if soft_fail_count >= caution_threshold:
        return _result(
            OverallResult.PASSED_WITH_CAUTION,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "soft_fail_threshold_reached",
        )

    if hard_pass_count > 0 and soft_fail_count == 0:
        return _result(
            OverallResult.PASSED,
            soft_fail_count,
            hard_pass_count,
            all_hard_not_applicable,
            "hard_pass_without_soft_fail",
        )

    return _result(
        OverallResult.PARTIALLY_PASSED,
        soft_fail_count,
        hard_pass_count,
        all_hard_not_applicable,
        "non_blocking_incomplete_confirmation",
    )


def resolve_recommended_actions(
    default_actions: Sequence[AllowedAction],
    constraint_results: Sequence[ConstraintEvaluationResult],
) -> tuple[AllowedAction, ...]:
    blocked: set[AllowedAction] = set()
    for result in constraint_results:
        if (
            result.constraint_type is not ConstraintType.HARD
            or result.status is not ConstraintStatus.FAIL
        ):
            continue
        if result.impact_on_decision is ImpactOnDecision.BLOCK_NEW_POSITION:
            blocked.add(AllowedAction.BUY)
        elif result.impact_on_decision is ImpactOnDecision.BLOCK_ADD_POSITION:
            blocked.add(AllowedAction.ADD_POSITION)

    return tuple(action for action in default_actions if action not in blocked)


def merge_confidence_cap(
    initial_cap: Decimal,
    adjustments: Sequence[ConfidenceAdjustment],
    *,
    review_threshold: Decimal = Decimal("0.5"),
) -> ConfidenceCapResult:
    if not Decimal("0") <= initial_cap <= Decimal("1"):
        raise DecisionLogicError("initial_cap must be between 0 and 1")
    if not Decimal("0") <= review_threshold <= Decimal("1"):
        raise DecisionLogicError("review_threshold must be between 0 and 1")

    source_order = {
        AdjustmentSource.PLAYBOOK: 0,
        AdjustmentSource.CONFLICT: 1,
        AdjustmentSource.VALIDATION: 2,
        AdjustmentSource.GUARDRAIL: 3,
    }
    ordered = sorted(
        enumerate(adjustments),
        key=lambda item: (source_order[item[1].source], item[0]),
    )

    cap = initial_cap
    steps: list[ConfidenceCapStep] = []
    for _, adjustment in ordered:
        cap_before = cap
        cap = max(Decimal("0"), cap - adjustment.amount)
        steps.append(
            ConfidenceCapStep(
                source=adjustment.source,
                source_ref=adjustment.source_ref,
                cap_before=cap_before,
                adjustment=adjustment.amount,
                cap_after=cap,
            )
        )

    return ConfidenceCapResult(
        initial_cap=initial_cap,
        final_cap=cap,
        review_threshold=review_threshold,
        requires_human_review=cap < review_threshold,
        steps=tuple(steps),
    )


def _result(
    overall_result: OverallResult,
    soft_fail_count: int,
    hard_pass_count: int,
    all_hard_not_applicable: bool,
    reason_code: str,
) -> OverallResultComputation:
    return OverallResultComputation(
        overall_result=overall_result,
        requires_human_review=(
            overall_result is OverallResult.REQUIRES_HUMAN_REVIEW
        ),
        soft_fail_count_total=soft_fail_count,
        hard_pass_count=hard_pass_count,
        all_hard_not_applicable=all_hard_not_applicable,
        reason_code=reason_code,
    )
