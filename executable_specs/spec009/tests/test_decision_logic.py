"""Tests for SPEC-009 Governance layer — Guardrails, Evaluator, Bounds, Contamination."""

import pytest

from crosslens_spec009.decision_logic import (
    aggregate_human_review_signals,
    apply_guardrails,
    check_evidence_contamination,
    compute_final_confidence_cap,
    narrow_bounds,
    resolve_decision_bounds,
    route_after_human_review,
    run_evaluator,
)
from crosslens_spec009.models import (
    ConfidenceCapAdjustment,
    ConfidenceCapReason,
    ContaminationLevel,
    ContaminationResult,
    EvaluationFinding,
    EvaluatorSeverity,
    GuardrailOverallStatus,
    OverallQuality,
    ResolvedDecisionBounds,
    RouteAction,
)


# ═══════════════════════════════════════════════════════════════════
# Guardrail Tests — apply_guardrails (§3.4)
# ═══════════════════════════════════════════════════════════════════

class TestGuardrailApply:
    """6 guardrail rules with branching paths."""

    def test_r1_no_return_promise_triggers_block_output(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "hold"],
            has_return_promise_language=True,
        )
        assert report.output_control == "block_output"
        assert report.overall_status == GuardrailOverallStatus.BLOCKED
        assert report.requires_human_review is True
        assert len(report.blocked_candidate_actions) == 0  # block_output is a control flag

    def test_r2_no_ungrounded_strong_opinion_with_low_confidence(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "add_position", "hold", "wait"],
            confidence=0.55,
            supporting_evidence_confidence=0.5,
        )
        assert "buy" in report.blocked_candidate_actions
        assert "add_position" in report.blocked_candidate_actions
        assert report.overall_status == GuardrailOverallStatus.REQUIRES_MODIFICATION

    def test_r2_does_not_trigger_with_high_confidence(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "hold"],
            supporting_evidence_confidence=0.85,
        )
        assert "buy" not in report.blocked_candidate_actions

    def test_r2_only_blocks_buy_and_add_position(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "add_position", "hold", "wait", "add_to_watchlist"],
            supporting_evidence_confidence=0.3,
        )
        assert "buy" in report.blocked_candidate_actions
        assert "add_position" in report.blocked_candidate_actions
        assert "hold" not in report.blocked_candidate_actions
        assert "wait" not in report.blocked_candidate_actions

    def test_r3_no_hidden_opposing_evidence(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold"],
            has_hidden_opposing_evidence=True,
        )
        assert report.requires_disclosure is True
        assert any(f.guardrail_id == "no_hidden_opposing_evidence" for f in report.findings)

    def test_r4_insufficient_data_guard(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "add_position", "reduce", "hold"],
            domain_status_by_domain={"fundamentals": "partial", "macro_meso": "partial"},
        )
        assert "buy" in report.blocked_candidate_actions
        assert "add_position" in report.blocked_candidate_actions
        assert "reduce" in report.blocked_candidate_actions

    def test_r4_does_not_trigger_when_all_domains_completed(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "hold"],
            domain_status_by_domain={"fundamentals": "completed", "sentiment": "completed"},
            supporting_evidence_confidence=0.9,
        )
        assert len(report.blocked_candidate_actions) == 0

    def test_r5_stale_data_guard(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold"],
            has_stale_constraint_exports=True,
        )
        assert report.requires_disclosure is True
        assert any(f.guardrail_id == "stale_data_guard" for f in report.findings)

    def test_r6_no_certainty_from_uncertain_input(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold"],
            confidence=0.85,
            primary_evidence_quality="low",
        )
        assert any(f.guardrail_id == "no_certainty_from_uncertain_input" for f in report.findings)
        assert len(report.confidence_cap_adjustments) >= 1
        assert report.confidence_cap_adjustments[0].cap_value == 0.65

    def test_r6_does_not_trigger_with_good_quality(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold"],
            confidence=0.85,
            primary_evidence_quality="high",
        )
        assert not any(f.guardrail_id == "no_certainty_from_uncertain_input" for f in report.findings)

    def test_overall_status_passed_when_no_findings(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold", "wait"],
            domain_status_by_domain={"fundamentals": "completed"},
            supporting_evidence_confidence=0.9,
        )
        assert report.overall_status == GuardrailOverallStatus.PASSED
        assert report.triggered is False

    def test_block_output_not_in_blocked_candidate_actions(self):
        """block_output is a control flag, validated by the model itself."""
        report = apply_guardrails(
            recommended_decision_bounds=["buy"],
            has_return_promise_language=True,
        )
        assert "block_output" not in report.blocked_candidate_actions
        assert report.output_control == "block_output"


# ═══════════════════════════════════════════════════════════════════
# narrow_bounds (§3.5)
# ═══════════════════════════════════════════════════════════════════

class TestNarrowBounds:

    def test_removes_blocked_actions(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy", "hold", "wait"],
            supporting_evidence_confidence=0.3,
        )
        narrowed = narrow_bounds(["buy", "hold", "wait"], report)
        assert "buy" not in narrowed
        assert "hold" in narrowed
        assert "wait" in narrowed

    def test_adds_wait_when_all_directional_removed(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy"],
            supporting_evidence_confidence=0.3,
        )
        narrowed = narrow_bounds(["buy"], report)
        assert "wait" in narrowed

    def test_only_removes_never_adds(self):
        report = apply_guardrails(
            recommended_decision_bounds=["hold"],
        )
        narrowed = narrow_bounds(["hold"], report)
        assert set(narrowed) == {"hold"}  # wait only added if directional actions empty

    def test_respects_guardrail_output_control(self):
        report = apply_guardrails(
            recommended_decision_bounds=["buy"],
            has_return_promise_language=True,
        )
        # narrow_bounds still processes — resolved_decision_bounds handles the block_output
        narrowed = narrow_bounds(["buy", "hold"], report)
        assert "buy" in narrowed  # not blocked via blocked_candidate_actions
        assert "hold" in narrowed


# ═══════════════════════════════════════════════════════════════════
# Evaluator Tests — run_evaluator (§4.4)
# ═══════════════════════════════════════════════════════════════════

class TestEvaluator:

    def test_acceptable_when_no_issues(self):
        report = run_evaluator(total_primary_evidence=5, computed_evidence_count=5)
        assert report.overall_quality == OverallQuality.ACCEPTABLE
        assert len(report.findings) == 0

    def test_high_interpreted_ratio_triggers_warning(self):
        report = run_evaluator(
            total_primary_evidence=10, computed_evidence_count=5, interpreted_evidence_count=5,
        )
        assert report.overall_quality == OverallQuality.ACCEPTABLE_WITH_CAVEATS
        assert "high_interpreted_ratio" in report.quality_flags
        assert len(report.confidence_cap_adjustments) > 0

    def test_no_computed_evidence_triggers_warning(self):
        report = run_evaluator(total_primary_evidence=5, computed_evidence_count=0)
        assert "no_computed_evidence" in report.quality_flags

    def test_internal_contradictions_cause_needs_revision(self):
        report = run_evaluator(
            total_primary_evidence=5, computed_evidence_count=5,
            has_internal_contradictions=True, contradiction_count=3,
        )
        assert report.overall_quality == OverallQuality.NEEDS_REVISION
        assert "internal_contradiction" in report.quality_flags

    def test_miscalibrated_confidence(self):
        report = run_evaluator(
            total_primary_evidence=5, computed_evidence_count=5,
            cards_confidence_above_0_8_with_low_data_quality=2,
        )
        assert "miscalibrated_confidence" in report.quality_flags

    def test_missing_required_evidence(self):
        report = run_evaluator(
            total_primary_evidence=5, computed_evidence_count=5,
            missing_required_evidence_count=3,
        )
        assert "incomplete_coverage" in report.quality_flags


# ═══════════════════════════════════════════════════════════════════
# Confidence Cap Merge — compute_final_confidence_cap (§4.5)
# ═══════════════════════════════════════════════════════════════════

class TestConfidenceCapMerge:

    def test_no_adjustments_returns_playbook_cap(self):
        cap, reasons, needs_review = compute_final_confidence_cap(
            playbook_recommended_cap=0.90,
        )
        assert cap == 0.90
        assert len(reasons) == 0
        assert needs_review is False

    def test_guardrail_takes_strictest(self):
        cap, reasons, _ = compute_final_confidence_cap(
            playbook_recommended_cap=1.0,
            guardrail_adjustments=[
                ConfidenceCapAdjustment(source="g1", cap_value=0.65),
                ConfidenceCapAdjustment(source="g2", cap_value=0.70),
            ],
        )
        assert cap == 0.65
        assert reasons[0].source_type == "guardrail"

    def test_evaluator_does_not_override_guardrail(self):
        cap, reasons, _ = compute_final_confidence_cap(
            playbook_recommended_cap=1.0,
            guardrail_adjustments=[ConfidenceCapAdjustment(source="g1", cap_value=0.65)],
            evaluator_adjustments=[ConfidenceCapAdjustment(source="e1", cap_value=0.60)],
        )
        assert cap == 0.60
        assert reasons[0].source_type == "guardrail"
        assert reasons[1].source_type == "evaluator"

    def test_preference_cannot_raise_cap(self):
        cap, reasons, _ = compute_final_confidence_cap(
            playbook_recommended_cap=1.0,
            guardrail_adjustments=[ConfidenceCapAdjustment(source="g1", cap_value=0.55)],
            preference_adjustments=[ConfidenceCapAdjustment(source="p1", cap_value=0.80)],
        )
        assert cap == 0.55

    def test_below_threshold_triggers_review(self):
        cap, reasons, needs_review = compute_final_confidence_cap(
            playbook_recommended_cap=1.0,
            guardrail_adjustments=[ConfidenceCapAdjustment(source="g1", cap_value=0.45)],
            review_threshold=0.50,
        )
        assert cap == 0.45
        assert needs_review is True

    def test_at_threshold_does_not_trigger_review(self):
        cap, _, needs_review = compute_final_confidence_cap(
            playbook_recommended_cap=0.50,
            review_threshold=0.50,
        )
        assert cap == 0.50
        assert needs_review is False


# ═══════════════════════════════════════════════════════════════════
# Human Review Aggregation — aggregate_human_review_signals (§5.2)
# ═══════════════════════════════════════════════════════════════════

class TestHumanReviewAggregation:

    def test_no_signals_no_review(self):
        requires, triggers = aggregate_human_review_signals()
        assert requires is False
        assert len(triggers) == 0

    def test_guardrail_triggers_review(self):
        requires, triggers = aggregate_human_review_signals(
            guardrail_requires_review=True,
            guardrail_report_id="gr_001",
        )
        assert requires is True
        assert triggers[0].source == "guardrail"

    def test_blocking_conflict_triggers_review(self):
        requires, triggers = aggregate_human_review_signals(
            has_blocking_conflict=True,
            conflict_report_id="cr_001",
        )
        assert requires is True
        assert triggers[0].source == "conflict_report"

    def test_playbook_requires_review(self):
        requires, triggers = aggregate_human_review_signals(
            playbook_overall_result="requires_human_review",
        )
        assert requires is True
        assert triggers[0].source == "playbook_evaluation"

    def test_confidence_cap_below_threshold(self):
        requires, triggers = aggregate_human_review_signals(
            resolved_confidence_cap=0.30,
            review_threshold=0.50,
        )
        assert requires is True
        assert triggers[0].source == "evaluator"

    def test_fundamentals_unavailable(self):
        requires, triggers = aggregate_human_review_signals(
            fundamentals_domain_status="unavailable",
        )
        assert requires is True
        assert triggers[0].source == "orchestration"

    def test_macro_partial_with_conflict(self):
        requires, triggers = aggregate_human_review_signals(
            macro_domain_status="partial",
            macro_has_conflict=True,
        )
        assert requires is True
        assert triggers[0].source == "orchestration"

    def test_fundamentals_error(self):
        requires, triggers = aggregate_human_review_signals(
            fundamentals_domain_status="error",
        )
        assert requires is True

    def test_fundamentals_insufficient_data_is_not_a_domain_status(self):
        """'insufficient_data' 不在 Registry domain_status 枚举中，不应触发 human review。"""
        requires, triggers = aggregate_human_review_signals(
            fundamentals_domain_status="insufficient_data",
        )
        assert requires is False


# ═══════════════════════════════════════════════════════════════════
# Route After Human Review — route_after_human_review (§5.3)
# ═══════════════════════════════════════════════════════════════════

class TestRouteAfterReview:

    def test_review_blocks_candidate(self):
        route = route_after_human_review(requires_review=True, triggers=[])
        assert route.action == RouteAction.BLOCK_CANDIDATE
        assert route.user_visible_status == "requires_human_review"

    def test_no_review_proceeds(self):
        route = route_after_human_review(requires_review=False)
        assert route.action == RouteAction.PROCEED_TO_CANDIDATE


# ═══════════════════════════════════════════════════════════════════
# Contamination Detection — check_evidence_contamination (§6.2)
# ═══════════════════════════════════════════════════════════════════

class TestContaminationDetection:

    def test_clean_evidence(self):
        result = check_evidence_contamination(
            generation_type="computed",
            determinism_level="computed",
        )
        assert result.contamination_level == ContaminationLevel.CLEAN

    def test_interpreted_is_contaminated(self):
        result = check_evidence_contamination(
            generation_type="interpreted",
            determinism_level="structured",
            evidence_id="ev_01",
        )
        assert result.contamination_level == ContaminationLevel.CONTAMINATED

    def test_low_determinism_is_potentially_contaminated(self):
        result = check_evidence_contamination(
            generation_type="structured",
            determinism_level="low",
            evidence_id="ev_02",
        )
        assert result.contamination_level == ContaminationLevel.POTENTIALLY_CONTAMINATED

    def test_recursive_lineage_detects_contamination(self):
        registry = {
            "ev_parent": {
                "generation_type": "interpreted",
                "determinism_level": "structured",
                "parent_evidence_refs": None,
            },
        }
        result = check_evidence_contamination(
            generation_type="structured",
            determinism_level="structured",
            evidence_id="ev_child",
            parent_evidence_refs=["ev_parent"],
            evidence_registry=registry,
        )
        assert result.contamination_level == ContaminationLevel.CONTAMINATED
        assert "ev_parent" in result.contamination_path
        assert "ev_child" in result.contamination_path

    def test_max_depth_exceeded(self):
        result = check_evidence_contamination(
            generation_type="structured",
            determinism_level="structured",
            max_depth=0,
        )
        assert result.contamination_level == ContaminationLevel.UNKNOWN
        assert result.reason == "max_depth_exceeded"

    def test_missing_parent_in_registry_is_skipped(self):
        result = check_evidence_contamination(
            generation_type="computed",
            determinism_level="computed",
            evidence_id="ev_child",
            parent_evidence_refs=["missing_ev"],
            evidence_registry={},
        )
        assert result.contamination_level == ContaminationLevel.CLEAN


# ═══════════════════════════════════════════════════════════════════
# Resolved Decision Bounds — resolve_decision_bounds (§8.1)
# ═══════════════════════════════════════════════════════════════════

class TestResolveDecisionBounds:
    """Complete six-step merge algorithm."""

    @staticmethod
    def _eval_report(**kw):
        return run_evaluator(total_primary_evidence=5, computed_evidence_count=5, **kw)

    @staticmethod
    def _gr_report(**kw):
        defaults = dict(
            recommended_decision_bounds=["buy", "hold", "wait"],
        )
        defaults.update(kw)
        return apply_guardrails(**defaults)

    def test_full_merge_basic_path(self):
        gr = self._gr_report()
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["buy", "hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
        )
        assert isinstance(result, ResolvedDecisionBounds)
        assert len(result.allowed_actions) > 0
        assert "buy" in result.allowed_actions or "hold" in result.allowed_actions
        assert len(result.reasoning) >= 1

    def test_guardrail_narrowing_in_bounds(self):
        gr = self._gr_report(supporting_evidence_confidence=0.3)
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["buy", "hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
        )
        assert "buy" not in result.allowed_actions

    def test_output_control_block_output_empties_allowed(self):
        gr = self._gr_report(has_return_promise_language=True)
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["buy", "hold"],
            guardrail_report=gr,
            evaluation_report=ev,
        )
        assert result.output_control == "block_output"
        assert len(result.allowed_actions) == 0  # block_output skips fallback "wait"

    def test_contamination_removes_directional_actions(self):
        gr = self._gr_report()
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["buy", "add_position", "hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
            contamination_results=[
                ContaminationResult(
                    contamination_level=ContaminationLevel.CONTAMINATED,
                    contamination_path=["ev_bad", "ev_good"],
                    reason="via lineage",
                ),
            ],
        )
        assert "buy" not in result.allowed_actions
        assert "add_position" not in result.allowed_actions
        assert len(result.contamination_findings) == 1

    def test_confidence_cap_below_threshold_triggers_review(self):
        gr = self._gr_report(
            confidence=0.85,
            primary_evidence_quality="low",  # triggers R6 → cap 0.65
        )
        ev = run_evaluator(
            total_primary_evidence=5, computed_evidence_count=5,
            cards_confidence_above_0_8_with_low_data_quality=3,
        )
        result = resolve_decision_bounds(
            playbook_bounds=["hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
            fundamentals_domain_status="completed",
            playbook_recommended_cap=1.0,
            review_threshold=0.70,
        )
        assert result.confidence_cap <= 0.65
        assert result.requires_human_review is True

    def test_playbook_overall_result_triggers_review(self):
        """playbook_overall_result='requires_human_review' must fire Source 3."""
        gr = self._gr_report()
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
            playbook_overall_result="requires_human_review",
        )
        assert result.requires_human_review is True
        playbook_triggers = [
            t for t in result.human_review_triggers
            if t.trigger_type.value == "playbook_requires_review"
        ]
        assert len(playbook_triggers) == 1

    def test_playbook_overall_result_default_does_not_trigger_review(self):
        """Default (empty) playbook_overall_result must not fire Source 3."""
        gr = self._gr_report()
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
        )
        playbook_triggers = [
            t for t in result.human_review_triggers
            if t.trigger_type.value == "playbook_requires_review"
        ]
        assert len(playbook_triggers) == 0

    def test_forbidden_combination_rejected(self):
        with pytest.raises(ValueError, match="forbidden.*combination"):
            ResolvedDecisionBounds(
                resolved_decision_bounds_id="rdb_001",
                task_id="task_001",
                run_id="run_001",
                allowed_actions=["buy", "reduce"],
                requires_human_review=False,
                confidence_cap=1.0,
            )

    def test_block_output_not_in_allowed_actions(self):
        with pytest.raises(ValueError, match="block_output"):
            ResolvedDecisionBounds(
                resolved_decision_bounds_id="rdb_001",
                task_id="task_001",
                run_id="run_001",
                allowed_actions=["block_output", "hold"],
                requires_human_review=False,
                confidence_cap=1.0,
            )

    def test_strong_buy_not_in_allowed_actions(self):
        with pytest.raises(ValueError, match="strong_buy"):
            ResolvedDecisionBounds(
                resolved_decision_bounds_id="rdb_001",
                task_id="task_001",
                run_id="run_001",
                allowed_actions=["strong_buy", "hold"],
                requires_human_review=False,
                confidence_cap=1.0,
            )

    def test_fundamentals_unavailable_triggers_review_in_bounds(self):
        gr = self._gr_report()
        ev = self._eval_report()
        result = resolve_decision_bounds(
            playbook_bounds=["hold", "wait"],
            guardrail_report=gr,
            evaluation_report=ev,
            fundamentals_domain_status="unavailable",
        )
        assert result.requires_human_review is True
        assert any(t.trigger_type.value == "fundamentals_unavailable" for t in result.human_review_triggers)


# ═══════════════════════════════════════════════════════════════════
# Model-Level Tests
# ═══════════════════════════════════════════════════════════════════

class TestModels:

    def test_guardrail_report_block_output_in_blocked_candidate_actions_fails(self):
        from crosslens_spec009.models import (
            Finding,
            GuardrailOverallStatus,
            GuardrailReport,
            GuardrailSeverity,
        )
        with pytest.raises(ValueError, match="block_output.*control flag"):
            GuardrailReport(
                guardrail_report_id="gr_001",
                task_id="task_001",
                run_id="run_001",
                triggered=True,
                overall_status=GuardrailOverallStatus.BLOCKED,
                blocked_candidate_actions=["block_output"],
                requires_human_review=True,
            )

    def test_resolved_bounds_requires_review_requires_triggers(self):
        with pytest.raises(ValueError, match="human_review_trigger"):
            ResolvedDecisionBounds(
                resolved_decision_bounds_id="rdb_001",
                task_id="task_001",
                run_id="run_001",
                allowed_actions=["hold"],
                requires_human_review=True,
                human_review_triggers=[],
                confidence_cap=1.0,
            )
