from decimal import Decimal

import pytest
from pydantic import ValidationError

from crosslens_spec006 import (
    AllowedAction,
    ApplicabilityStatus,
    ConfidenceAdjustment,
    ConstraintEvaluationResult,
    ConstraintStatus,
    ConstraintType,
    ImpactOnDecision,
    OverallResult,
    ReviewSignal,
    aggregate_multi_rule,
    compute_overall_result,
    merge_confidence_cap,
    resolve_recommended_actions,
)


def result(
    constraint_id: str,
    constraint_type: ConstraintType,
    status: ConstraintStatus,
    impact: ImpactOnDecision,
) -> ConstraintEvaluationResult:
    return ConstraintEvaluationResult(
        constraint_id=constraint_id,
        constraint_type=constraint_type,
        status=status,
        impact_on_decision=impact,
    )


@pytest.mark.parametrize(
    ("logic", "statuses", "expected"),
    [
        ("all", [ConstraintStatus.PASS, ConstraintStatus.PASS], ConstraintStatus.PASS),
        ("all", [ConstraintStatus.FAIL, ConstraintStatus.ERROR], ConstraintStatus.FAIL),
        (
            "all",
            [ConstraintStatus.PASS, ConstraintStatus.INSUFFICIENT_DATA],
            ConstraintStatus.INSUFFICIENT_DATA,
        ),
        ("any", [ConstraintStatus.PASS, ConstraintStatus.ERROR], ConstraintStatus.PASS),
        ("any", [ConstraintStatus.FAIL, ConstraintStatus.FAIL], ConstraintStatus.FAIL),
        (
            "any",
            [ConstraintStatus.FAIL, ConstraintStatus.INSUFFICIENT_DATA],
            ConstraintStatus.PARTIAL,
        ),
        (
            "any",
            [ConstraintStatus.INSUFFICIENT_DATA, ConstraintStatus.STALE_DATA],
            ConstraintStatus.INSUFFICIENT_DATA,
        ),
        (
            "any",
            [ConstraintStatus.NOT_APPLICABLE],
            ConstraintStatus.NOT_APPLICABLE,
        ),
    ],
)
def test_multi_rule_aggregation(logic, statuses, expected):
    assert aggregate_multi_rule(statuses, logic) is expected


def test_ambiguous_label_ref_requires_human_review():
    hard_pass = result(
        "hard-pass",
        ConstraintType.HARD,
        ConstraintStatus.PASS,
        ImpactOnDecision.SUPPORT,
    )

    computed = compute_overall_result(
        [hard_pass],
        review_signals=[ReviewSignal.AMBIGUOUS_LABEL_REF],
    )

    assert computed.overall_result is OverallResult.REQUIRES_HUMAN_REVIEW
    assert computed.requires_human_review is True


def test_human_review_soft_fail_is_counted_but_short_circuits_caution():
    constraints = [
        result(
            "hard-pass",
            ConstraintType.HARD,
            ConstraintStatus.PASS,
            ImpactOnDecision.SUPPORT,
        ),
        result(
            "review-soft-fail",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.REQUIRE_HUMAN_REVIEW,
        ),
        result(
            "caution-soft-fail",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.LOWER_CONFIDENCE,
        ),
    ]

    computed = compute_overall_result(constraints)

    assert computed.soft_fail_count_total == 2
    assert computed.overall_result is OverallResult.REQUIRES_HUMAN_REVIEW


def test_hard_fail_blocks_new_buy_even_with_unresolved_hard_result():
    constraints = [
        result(
            "blocking-hard",
            ConstraintType.HARD,
            ConstraintStatus.FAIL,
            ImpactOnDecision.BLOCK_NEW_POSITION,
        ),
        result(
            "missing-hard",
            ConstraintType.HARD,
            ConstraintStatus.INSUFFICIENT_DATA,
            ImpactOnDecision.NEED_MORE_DATA,
        ),
    ]

    computed = compute_overall_result(constraints)

    assert computed.overall_result is OverallResult.NOT_PASSED_FOR_NEW_BUY


def test_add_position_has_an_explicit_result_branch():
    blocking_add = result(
        "blocking-add",
        ConstraintType.HARD,
        ConstraintStatus.FAIL,
        ImpactOnDecision.BLOCK_ADD_POSITION,
    )

    computed = compute_overall_result([blocking_add])

    assert computed.overall_result is OverallResult.NOT_PASSED_FOR_ADD_POSITION


@pytest.mark.parametrize(
    ("soft_fail_count", "expected"),
    [
        (0, OverallResult.PASSED),
        (1, OverallResult.PARTIALLY_PASSED),
        (2, OverallResult.PASSED_WITH_CAUTION),
    ],
)
def test_hard_pass_soft_fail_threshold(soft_fail_count, expected):
    constraints = [
        result(
            "hard-pass",
            ConstraintType.HARD,
            ConstraintStatus.PASS,
            ImpactOnDecision.SUPPORT,
        )
    ]
    constraints.extend(
        result(
            f"soft-{index}",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.LOWER_CONFIDENCE,
        )
        for index in range(soft_fail_count)
    )

    assert compute_overall_result(constraints).overall_result is expected


def test_all_hard_not_applicable_never_passes():
    not_applicable = result(
        "hard-na",
        ConstraintType.HARD,
        ConstraintStatus.NOT_APPLICABLE,
        ImpactOnDecision.NEUTRAL,
    )

    computed = compute_overall_result([not_applicable])

    assert computed.overall_result is OverallResult.PARTIALLY_PASSED
    assert computed.all_hard_not_applicable is True


def test_partially_passed_does_not_remove_buy():
    constraints = [
        result(
            "hard-pass",
            ConstraintType.HARD,
            ConstraintStatus.PASS,
            ImpactOnDecision.SUPPORT,
        ),
        result(
            "soft-fail",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.LOWER_CONFIDENCE,
        ),
    ]
    computed = compute_overall_result(constraints)
    actions = resolve_recommended_actions(
        [AllowedAction.BUY, AllowedAction.WAIT],
        constraints,
    )

    assert computed.overall_result is OverallResult.PARTIALLY_PASSED
    assert AllowedAction.BUY in actions


def test_hard_block_removes_buy_from_recommended_actions():
    constraints = [
        result(
            "hard-fail",
            ConstraintType.HARD,
            ConstraintStatus.FAIL,
            ImpactOnDecision.BLOCK_NEW_POSITION,
        )
    ]

    actions = resolve_recommended_actions(
        [AllowedAction.BUY, AllowedAction.WAIT],
        constraints,
    )

    assert actions == (AllowedAction.WAIT,)


def test_not_applicable_playbook_is_resolved_before_constraint_tree():
    review_soft_fail = result(
        "review-soft-fail",
        ConstraintType.SOFT,
        ConstraintStatus.FAIL,
        ImpactOnDecision.REQUIRE_HUMAN_REVIEW,
    )

    computed = compute_overall_result(
        [review_soft_fail],
        applicability_status=ApplicabilityStatus.NOT_APPLICABLE,
    )

    assert computed.overall_result is OverallResult.NOT_SUITABLE_FOR_PLAYBOOK


def test_invalid_mvp_hard_fail_contract_is_rejected():
    with pytest.raises(ValidationError):
        result(
            "invalid-hard-fail",
            ConstraintType.HARD,
            ConstraintStatus.FAIL,
            ImpactOnDecision.LOWER_CONFIDENCE,
        )


def test_soft_constraint_rejects_block_new_position():
    with pytest.raises(ValidationError):
        result(
            "soft-block-buy",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.BLOCK_NEW_POSITION,
        )


def test_soft_constraint_rejects_block_add_position():
    with pytest.raises(ValidationError):
        result(
            "soft-block-add",
            ConstraintType.SOFT,
            ConstraintStatus.FAIL,
            ImpactOnDecision.BLOCK_ADD_POSITION,
        )


def test_soft_constraint_rejects_need_more_data():
    with pytest.raises(ValidationError):
        result(
            "soft-need-data",
            ConstraintType.SOFT,
            ConstraintStatus.INSUFFICIENT_DATA,
            ImpactOnDecision.NEED_MORE_DATA,
        )


def test_soft_constraint_allows_require_human_review():
    # This should not raise — require_human_review is valid for Soft
    _ = result(
        "soft-review",
        ConstraintType.SOFT,
        ConstraintStatus.FAIL,
        ImpactOnDecision.REQUIRE_HUMAN_REVIEW,
    )


def test_confidence_adjustments_use_canonical_source_order():
    merged = merge_confidence_cap(
        Decimal("0.60"),
        [
            ConfidenceAdjustment(
                source="guardrail", source_ref="g-1", amount=Decimal("0.04")
            ),
            ConfidenceAdjustment(
                source="playbook", source_ref="p-1", amount=Decimal("0.05")
            ),
            ConfidenceAdjustment(
                source="validation", source_ref="v-1", amount=Decimal("0.02")
            ),
            ConfidenceAdjustment(
                source="conflict", source_ref="c-1", amount=Decimal("0.01")
            ),
        ],
    )

    assert [step.source.value for step in merged.steps] == [
        "playbook",
        "conflict",
        "validation",
        "guardrail",
    ]
    assert merged.final_cap == Decimal("0.48")
    assert merged.requires_human_review is True


def test_confidence_threshold_is_strictly_less_than_point_five():
    merged = merge_confidence_cap(
        Decimal("0.55"),
        [
            ConfidenceAdjustment(
                source="playbook", source_ref="p-1", amount=Decimal("0.05")
            )
        ],
    )

    assert merged.final_cap == Decimal("0.50")
    assert merged.requires_human_review is False


def test_confidence_cap_clamps_only_at_zero():
    merged = merge_confidence_cap(
        Decimal("0.10"),
        [
            ConfidenceAdjustment(
                source="playbook", source_ref="p-1", amount=Decimal("0.70")
            )
        ],
    )

    assert merged.final_cap == Decimal("0")
    assert merged.steps[0].cap_after == Decimal("0")
    assert merged.requires_human_review is True


def test_contracts_forbid_unknown_fields():
    with pytest.raises(ValidationError):
        ConstraintEvaluationResult(
            constraint_id="hard-pass",
            constraint_type="hard",
            status="pass",
            impact_on_decision="support",
            unexpected=True,
        )
