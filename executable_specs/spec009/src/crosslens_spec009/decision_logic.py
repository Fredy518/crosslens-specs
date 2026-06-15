"""Executable governance decision logic for SPEC-009."""

from __future__ import annotations

from collections.abc import Sequence

from .models import (
    ConfidenceCapAdjustment,
    ConfidenceCapReason,
    ContaminationFinding,
    ContaminationLevel,
    ContaminationResult,
    EvaluationFinding,
    EvaluationReport,
    EvaluatorDimension,
    EvaluatorSeverity,
    Finding,
    GuardrailOverallStatus,
    GuardrailReport,
    GuardrailSeverity,
    HumanReviewTrigger,
    HumanReviewTriggerType,
    OverallQuality,
    ReasonEntry,
    ResolvedDecisionBounds,
    RouteAction,
    RouteDecision,
)


# ═══════════════════════════════════════════════════════════════════
# §3.4: apply_guardrails
# ═══════════════════════════════════════════════════════════════════

def apply_guardrails(
    recommended_decision_bounds: list[str],
    domain_status_by_domain: dict[str, str] | None = None,
    confidence: float = 0.5,
    supporting_evidence_confidence: float | None = None,
    has_return_promise_language: bool = False,
    has_hidden_opposing_evidence: bool = False,
    has_stale_constraint_exports: bool = False,
    primary_evidence_quality: str = "medium",
) -> GuardrailReport:
    """
    Guardrail decision tree. Returns GuardrailReport.

    6 rules executed in order (§3.3):
    R1: no_return_promise — block_output (terminates immediately)
    R2: no_ungrounded_strong_opinion — buy/add_position + low confidence → downgrade
    R3: no_hidden_opposing_evidence — require_disclosure
    R4: insufficient_data_guard — required domain insufficient → cap actions
    R5: stale_data_guard — stale data → require_freshness_warning
    R6: no_certainty_from_uncertain_input — low evidence quality → cap_confidence
    """
    findings: list[Finding] = []
    blocked_candidate_actions: set[str] = set()
    output_control: str | None = None
    requires_disclosure = False
    confidence_cap_adjustments: list[ConfidenceCapAdjustment] = []

    # Phase 1: Output safety checks
    # R1: no_return_promise
    if has_return_promise_language:
        findings.append(_finding("no_return_promise", GuardrailSeverity.CRITICAL, "block_output"))
        output_control = "block_output"
        return _make_guardrail_report(
            findings=findings,
            overall_status=GuardrailOverallStatus.BLOCKED,
            blocked_candidate_actions=[],
            output_control=output_control,
            confidence_cap_adjustments=confidence_cap_adjustments,
            requires_human_review=True,
        )

    # R2: no_ungrounded_strong_opinion
    for action in {"buy", "add_position"} & set(recommended_decision_bounds):
        if (supporting_evidence_confidence or 0.0) < 0.7:
            findings.append(_finding("no_ungrounded_strong_opinion", GuardrailSeverity.CRITICAL, "downgrade_to_hold_or_wait"))
            blocked_candidate_actions.add(action)

    # R3: no_hidden_opposing_evidence
    if has_hidden_opposing_evidence:
        findings.append(_finding("no_hidden_opposing_evidence", GuardrailSeverity.HIGH, "require_disclosure"))
        requires_disclosure = True

    # Phase 2: Data sufficiency checks
    # R4: insufficient_data_guard
    if domain_status_by_domain and _has_insufficient_required_domain(domain_status_by_domain):
        findings.append(_finding("insufficient_data_guard", GuardrailSeverity.HIGH, "cap_action_to_wait_or_watchlist"))
        blocked_candidate_actions.update({"buy", "add_position", "reduce"})

    # R5: stale_data_guard
    if has_stale_constraint_exports:
        findings.append(_finding("stale_data_guard", GuardrailSeverity.MEDIUM, "require_freshness_warning"))
        requires_disclosure = True

    # Phase 3: Model output safety checks
    # R6: no_certainty_from_uncertain_input
    quality_order = {"high": 4, "medium": 3, "low": 2, "unavailable": 1, "unknown": 0}
    if confidence > 0.8 and quality_order.get(primary_evidence_quality, 3) < 3:
        findings.append(_finding("no_certainty_from_uncertain_input", GuardrailSeverity.HIGH, "cap_confidence"))
        confidence_cap_adjustments.append(ConfidenceCapAdjustment(
            source="guardrail:no_certainty_from_uncertain_input",
            reason="primary supporting evidence quality < medium",
            cap_value=0.65,
        ))

    # Phase 4: Determine overall_status
    has_block = any(f.action == "block_output" for f in findings)
    has_critical = any(f.severity == GuardrailSeverity.CRITICAL for f in findings)
    has_high = any(f.severity == GuardrailSeverity.HIGH for f in findings)

    if has_block:
        overall_status = GuardrailOverallStatus.BLOCKED
    elif has_critical:
        overall_status = GuardrailOverallStatus.REQUIRES_MODIFICATION
    elif has_high:
        overall_status = GuardrailOverallStatus.PASSED_WITH_CONSTRAINTS
    else:
        overall_status = GuardrailOverallStatus.PASSED

    return _make_guardrail_report(
        findings=findings,
        overall_status=overall_status,
        blocked_candidate_actions=sorted(blocked_candidate_actions),
        output_control=output_control,
        requires_disclosure=requires_disclosure,
        confidence_cap_adjustments=confidence_cap_adjustments,
        requires_human_review=(has_critical or has_block),
    )


# ═══════════════════════════════════════════════════════════════════
# §3.5: narrow_bounds
# ═══════════════════════════════════════════════════════════════════

def narrow_bounds(
    playbook_bounds: list[str],
    guardrail_report: GuardrailReport,
) -> list[str]:
    """
    Narrow Playbook-recommended bounds by removing Guardrail-blocked actions.

    Invariants:
    1. Can only remove actions, never add.
    2. Cannot restore actions already removed by Playbook.
    3. Narrowing is recorded in Decision Trace.
    """
    narrowed = sorted(set(playbook_bounds) - set(guardrail_report.blocked_candidate_actions))

    directional_actions = {"buy", "add_position", "reduce", "hold"}
    if not (set(narrowed) & directional_actions):
        narrowed.append("wait")
        narrowed = sorted(set(narrowed))

    return narrowed


# ═══════════════════════════════════════════════════════════════════
# §4.4: run_evaluator
# ═══════════════════════════════════════════════════════════════════

def run_evaluator(
    computed_evidence_count: int = 0,
    interpreted_evidence_count: int = 0,
    total_primary_evidence: int = 0,
    has_internal_contradictions: bool = False,
    contradiction_count: int = 0,
    cards_confidence_above_0_8_with_low_data_quality: int = 0,
    missing_required_evidence_count: int = 0,
) -> EvaluationReport:
    """
    Four-dimension quality evaluation (§4.3).

    Checks:
    1. evidence_quality — interpreted ratio, computed evidence presence
    2. reasoning_coherence — internal contradictions
    3. confidence_calibration — high confidence + low data quality mismatch
    4. completeness — missing required evidence
    """
    findings: list[EvaluationFinding] = []
    quality_flags: list[str] = []
    confidence_cap_adjustments: list[ConfidenceCapAdjustment] = []

    # Dimension 1: Evidence quality
    if total_primary_evidence > 0:
        interpreted_ratio = interpreted_evidence_count / total_primary_evidence
        if interpreted_ratio > 0.4:
            findings.append(EvaluationFinding(
                dimension=EvaluatorDimension.EVIDENCE_QUALITY,
                severity=EvaluatorSeverity.WARNING,
                description=f"Interpreted Evidence 占比 {interpreted_ratio:.0%}，超过 40% 阈值",
                recommended_action="consider_regenerating_with_better_data",
            ))
            quality_flags.append("high_interpreted_ratio")
            confidence_cap_adjustments.append(ConfidenceCapAdjustment(
                source="evaluator:high_interpreted_ratio",
                reason=f"Interpreted Evidence 占比 {interpreted_ratio:.0%}",
                cap_value=0.60,
            ))

        if computed_evidence_count == 0:
            findings.append(EvaluationFinding(
                dimension=EvaluatorDimension.EVIDENCE_QUALITY,
                severity=EvaluatorSeverity.WARNING,
                description="无 Computed Evidence 支撑关键结论",
                recommended_action="review_evidence_sources",
            ))
            quality_flags.append("no_computed_evidence")
            confidence_cap_adjustments.append(ConfidenceCapAdjustment(
                source="evaluator:no_computed_evidence",
                reason="关键结论无 Computed Evidence 支撑",
                cap_value=0.55,
            ))

    # Dimension 2: Reasoning coherence
    if has_internal_contradictions:
        findings.append(EvaluationFinding(
            dimension=EvaluatorDimension.REASONING_COHERENCE,
            severity=EvaluatorSeverity.ERROR,
            description=f"检测到 {contradiction_count} 处推理矛盾",
            details=[],
            recommended_action="review_and_correct",
        ))
        quality_flags.append("internal_contradiction")

    # Dimension 3: Confidence calibration
    if cards_confidence_above_0_8_with_low_data_quality > 0:
        findings.append(EvaluationFinding(
            dimension=EvaluatorDimension.CONFIDENCE_CALIBRATION,
            severity=EvaluatorSeverity.WARNING,
            description=f"{cards_confidence_above_0_8_with_low_data_quality} 张 Card 置信度 ≥ 0.80 与 data_quality=low 不匹配",
            recommended_action="lower_confidence",
        ))
        quality_flags.append("miscalibrated_confidence")

    # Dimension 4: Completeness
    if missing_required_evidence_count > 0:
        findings.append(EvaluationFinding(
            dimension=EvaluatorDimension.COMPLETENESS,
            severity=EvaluatorSeverity.WARNING,
            description=f"缺失 {missing_required_evidence_count} 项必需证据",
            recommended_action="request_missing_data",
        ))
        quality_flags.append("incomplete_coverage")

    # Phase 5: Determine overall_quality
    has_error = any(f.severity == EvaluatorSeverity.ERROR for f in findings)
    has_warning = any(f.severity == EvaluatorSeverity.WARNING for f in findings)

    if has_error:
        overall_quality = OverallQuality.NEEDS_REVISION
    elif has_warning:
        overall_quality = OverallQuality.ACCEPTABLE_WITH_CAVEATS
    else:
        overall_quality = OverallQuality.ACCEPTABLE

    return EvaluationReport(
        evaluation_report_id="eval_001",
        task_id="task_001",
        run_id="run_001",
        findings=findings,
        quality_flags=quality_flags,
        overall_quality=overall_quality,
        confidence_cap_adjustments=confidence_cap_adjustments,
    )


# ═══════════════════════════════════════════════════════════════════
# §4.5: compute_final_confidence_cap
# ═══════════════════════════════════════════════════════════════════

def compute_final_confidence_cap(
    playbook_recommended_cap: float = 1.0,
    guardrail_adjustments: Sequence[ConfidenceCapAdjustment] | None = None,
    evaluator_adjustments: Sequence[ConfidenceCapAdjustment] | None = None,
    preference_adjustments: Sequence[ConfidenceCapAdjustment] | None = None,
    review_threshold: float = 0.50,
) -> tuple[float, list[ConfidenceCapReason], bool]:
    """
    Three-layer confidence cap merge (§4.5).

    Priority: Guardrail > Evaluator > Preference.
    Each layer takes the strictest (lowest) cap value.
    Cap can only decrease (one-way narrowing).
    Final cap < review_threshold → requires_human_review.
    """
    reasons: list[ConfidenceCapReason] = []
    current_cap = min(max(playbook_recommended_cap, 0.0), 1.0)

    # Layer 1: Guardrail (highest priority)
    if guardrail_adjustments:
        strictest = min(adj.cap_value for adj in guardrail_adjustments)
        if strictest < current_cap:
            current_cap = strictest
            reasons.append(ConfidenceCapReason(
                source_type="guardrail",
                source_ref=guardrail_adjustments[0].source,
                reason="Guardrail triggered confidence cap narrowing",
                effect=f"cap_confidence_at_{current_cap}",
            ))

    # Layer 2: Evaluator
    if evaluator_adjustments:
        strictest = min(adj.cap_value for adj in evaluator_adjustments)
        if strictest < current_cap:
            current_cap = strictest
            reasons.append(ConfidenceCapReason(
                source_type="evaluator",
                source_ref=evaluator_adjustments[0].source,
                reason="Evaluator detected quality issues, lowering confidence cap",
                effect=f"cap_confidence_at_{current_cap}",
            ))

    # Layer 3: Preference (lowest priority)
    if preference_adjustments:
        strictest = min(adj.cap_value for adj in preference_adjustments)
        if strictest < current_cap:
            current_cap = strictest
            reasons.append(ConfidenceCapReason(
                source_type="preference",
                source_ref=preference_adjustments[0].source,
                reason="Playbook Preference adjusted confidence cap",
                effect=f"cap_confidence_at_{current_cap}",
            ))

    requires_human_review = current_cap < review_threshold
    return current_cap, reasons, requires_human_review


# ═══════════════════════════════════════════════════════════════════
# §5.2: aggregate_human_review_signals
# ═══════════════════════════════════════════════════════════════════

def aggregate_human_review_signals(
    guardrail_requires_review: bool = False,
    guardrail_report_id: str = "",
    has_blocking_conflict: bool = False,
    conflict_report_id: str = "",
    playbook_overall_result: str = "",
    resolved_confidence_cap: float = 1.0,
    review_threshold: float = 0.50,
    macro_domain_status: str = "unknown",
    fundamentals_domain_status: str = "completed",
    macro_has_conflict: bool = False,
) -> tuple[bool, list[HumanReviewTrigger]]:
    """
    Aggregate human review signals from six sources (§5.2).
    """
    triggers: list[HumanReviewTrigger] = []
    requires_review = False

    # Source 1: Guardrail
    if guardrail_requires_review:
        triggers.append(HumanReviewTrigger(
            source="guardrail",
            source_ref=guardrail_report_id,
            trigger_type=HumanReviewTriggerType.GUARDRAIL_BLOCK_OR_CRITICAL,
            description="Guardrail triggered human review",
        ))
        requires_review = True

    # Source 2: Conflict Report
    if has_blocking_conflict:
        triggers.append(HumanReviewTrigger(
            source="conflict_report",
            source_ref=conflict_report_id,
            trigger_type=HumanReviewTriggerType.BLOCKING_CONFLICT,
            description="Blocking conflict detected",
        ))
        requires_review = True

    # Source 3: Playbook requires review
    if playbook_overall_result == "requires_human_review":
        triggers.append(HumanReviewTrigger(
            source="playbook_evaluation",
            source_ref="playbook_evaluation_report",
            trigger_type=HumanReviewTriggerType.PLAYBOOK_REQUIRES_REVIEW,
            description="Playbook Evaluation cannot determine result automatically",
        ))
        requires_review = True

    # Source 4: confidence_cap < threshold
    if resolved_confidence_cap < review_threshold:
        triggers.append(HumanReviewTrigger(
            source="evaluator",
            source_ref="evaluation_report",
            trigger_type=HumanReviewTriggerType.CONFIDENCE_CAP_BELOW_THRESHOLD,
            description=f"Final confidence_cap = {resolved_confidence_cap} < {review_threshold}",
        ))
        requires_review = True

    # Source 5: Macro partial + conflict
    if macro_domain_status == "partial" and macro_has_conflict:
        triggers.append(HumanReviewTrigger(
            source="orchestration",
            source_ref=conflict_report_id,
            trigger_type=HumanReviewTriggerType.MACRO_PARTIAL_WITH_CONFLICT,
            description="Macro/Meso domain partial with macro_regime_vs_playbook conflict",
        ))
        requires_review = True

    # Source 6: Fundamentals unavailable
    if fundamentals_domain_status in {"unavailable", "error"}:
        triggers.append(HumanReviewTrigger(
            source="orchestration",
            source_ref="task_config",
            trigger_type=HumanReviewTriggerType.FUNDAMENTALS_UNAVAILABLE,
            description="Fundamentals domain unavailable — cannot generate Decision Candidate",
        ))
        requires_review = True

    return requires_review, triggers


# ═══════════════════════════════════════════════════════════════════
# §5.3: route_after_human_review
# ═══════════════════════════════════════════════════════════════════

def route_after_human_review(
    requires_review: bool,
    triggers: list[HumanReviewTrigger] | None = None,
) -> RouteDecision:
    """Route to block_candidate or proceed_to_candidate."""
    if requires_review:
        return RouteDecision(
            action=RouteAction.BLOCK_CANDIDATE,
            user_visible_status="requires_human_review",
            user_visible_reason=_build_review_reason(triggers or []),
            next_step="present_to_user_for_review",
        )
    return RouteDecision(
        action=RouteAction.PROCEED_TO_CANDIDATE,
        user_visible_status=None,
        next_step="generate_candidate",
    )


# ═══════════════════════════════════════════════════════════════════
# §6.2: check_evidence_contamination
# ═══════════════════════════════════════════════════════════════════

def check_evidence_contamination(
    generation_type: str,
    determinism_level: str,
    evidence_id: str = "",
    parent_evidence_refs: list[str] | None = None,
    evidence_registry: dict[str, dict] | None = None,
    max_depth: int = 3,
) -> ContaminationResult:
    """
    Recursive evidence contamination check (§6.2).

    Contamination definition:
    - Any ancestor with generation_type=interpreted → contaminated
    - Any ancestor with determinism_level=low → potentially_contaminated
    """
    if max_depth <= 0:
        return ContaminationResult(
            contamination_level=ContaminationLevel.UNKNOWN,
            contamination_path=[],
            reason="max_depth_exceeded",
        )

    # Check self
    if generation_type == "interpreted":
        return ContaminationResult(
            contamination_level=ContaminationLevel.CONTAMINATED,
            contamination_path=[evidence_id] if evidence_id else [],
            reason=f"Evidence {evidence_id} is itself Interpreted",
        )

    if determinism_level == "low":
        return ContaminationResult(
            contamination_level=ContaminationLevel.POTENTIALLY_CONTAMINATED,
            contamination_path=[evidence_id] if evidence_id else [],
            reason=f"Evidence {evidence_id} has determinism_level=low",
        )

    # Check lineage (recursive)
    if parent_evidence_refs and evidence_registry:
        for parent_ref in parent_evidence_refs:
            parent = evidence_registry.get(parent_ref)
            if parent is None:
                continue

            child_result = check_evidence_contamination(
                generation_type=parent.get("generation_type", ""),
                determinism_level=parent.get("determinism_level", ""),
                evidence_id=parent_ref,
                parent_evidence_refs=parent.get("parent_evidence_refs"),
                evidence_registry=evidence_registry,
                max_depth=max_depth - 1,
            )
            if child_result.contamination_level != ContaminationLevel.CLEAN:
                full_path = child_result.contamination_path + ([evidence_id] if evidence_id else [])
                return ContaminationResult(
                    contamination_level=child_result.contamination_level,
                    contamination_path=full_path,
                    reason=f"Via lineage: {child_result.reason}",
                )

    return ContaminationResult(
        contamination_level=ContaminationLevel.CLEAN,
        contamination_path=[],
        reason="",
    )


# ═══════════════════════════════════════════════════════════════════
# §8.1: resolve_decision_bounds (complete merge algorithm)
# ═══════════════════════════════════════════════════════════════════

def resolve_decision_bounds(
    playbook_bounds: list[str],
    guardrail_report: GuardrailReport,
    evaluation_report: EvaluationReport,
    conflict_has_blocking: bool = False,
    conflict_report_id: str = "",
    playbook_recommended_cap: float = 1.0,
    preference_adjustments: Sequence[ConfidenceCapAdjustment] | None = None,
    contamination_results: Sequence[ContaminationResult] | None = None,
    macro_domain_status: str = "unknown",
    fundamentals_domain_status: str = "completed",
    macro_has_conflict: bool = False,
    review_threshold: float = 0.50,
) -> ResolvedDecisionBounds:
    """
    Six-step bounds resolution (§8.1):
    1. Initial bounds from Playbook
    2. Guardrail narrowing
    3. Contamination detection adjustments
    4. Evaluator confidence_cap adjustments
    5. Human review signal aggregation
    6. Final bounds check
    """
    reasons: list[ReasonEntry] = []
    applied_rules: list[str] = []

    # Step 1: Initial bounds
    allowed = set(playbook_bounds)
    reasons.append(ReasonEntry(
        source="playbook_evaluation",
        action="initial_bounds",
        detail=f"Playbook recommended: {playbook_bounds}",
    ))

    # Step 2: Guardrail narrowing
    for blocked in guardrail_report.blocked_candidate_actions:
        if blocked in allowed:
            allowed.discard(blocked)
            reasons.append(ReasonEntry(
                source="guardrail",
                action="remove",
                detail=f"Guardrail removed '{blocked}'",
            ))
            applied_rules.append(f"guardrail:block_{blocked}")

    output_control = guardrail_report.output_control
    if output_control == "block_output":
        # block_output terminates the entire run — clear bounds regardless
        allowed = set()

    # Step 3: Contamination detection
    contaminations: list[ContaminationFinding] = []
    if contamination_results:
        for cr in contamination_results:
            if cr.contamination_level in {
                ContaminationLevel.CONTAMINATED,
                ContaminationLevel.POTENTIALLY_CONTAMINATED,
            }:
                contaminations.append(ContaminationFinding(
                    evidence_id=cr.contamination_path[0] if cr.contamination_path else "unknown",
                    contamination_level=cr.contamination_level,
                    contamination_path=cr.contamination_path,
                    reason=cr.reason,
                ))

    if contaminations:
        # Remove directional actions from potentially contaminated evidence
        allowed.discard("buy")
        allowed.discard("add_position")
        reasons.append(ReasonEntry(
            source="contamination_detection",
            action="remove",
            detail=f"Detected {len(contaminations)} contamination issue(s)",
        ))

    # Step 4: Evaluator confidence_cap adjustments
    confidence_cap, cap_reasons, cap_triggers_review = compute_final_confidence_cap(
        playbook_recommended_cap=playbook_recommended_cap,
        guardrail_adjustments=guardrail_report.confidence_cap_adjustments,
        evaluator_adjustments=evaluation_report.confidence_cap_adjustments,
        preference_adjustments=preference_adjustments,
        review_threshold=review_threshold,
    )

    # Step 5: Human review aggregation
    requires_review, review_triggers = aggregate_human_review_signals(
        guardrail_requires_review=guardrail_report.requires_human_review,
        guardrail_report_id=guardrail_report.guardrail_report_id,
        has_blocking_conflict=conflict_has_blocking,
        conflict_report_id=conflict_report_id,
        playbook_overall_result="",  # resolved from playbook earlier
        resolved_confidence_cap=confidence_cap,
        review_threshold=review_threshold,
        macro_domain_status=macro_domain_status,
        fundamentals_domain_status=fundamentals_domain_status,
        macro_has_conflict=macro_has_conflict,
    )
    requires_review = requires_review or cap_triggers_review or guardrail_report.requires_human_review

    # Step 6: Final bounds check
    if not allowed and output_control != "block_output":
        allowed = {"wait"}

    return ResolvedDecisionBounds(
        resolved_decision_bounds_id="rdb_001",
        task_id=guardrail_report.task_id,
        run_id=guardrail_report.run_id,
        allowed_actions=sorted(allowed),
        blocked_candidate_actions=sorted(guardrail_report.blocked_candidate_actions),
        output_control=output_control,
        requires_human_review=requires_review,
        human_review_triggers=review_triggers,
        confidence_cap=round(confidence_cap, 2),
        confidence_cap_reason=cap_reasons,
        applied_rules=applied_rules,
        reasoning=reasons,
        contamination_findings=contaminations,
    )


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _finding(
    guardrail_id: str, severity: GuardrailSeverity, action: str
) -> Finding:
    return Finding(
        guardrail_id=guardrail_id,
        severity=severity,
        action=action,
    )


def _make_guardrail_report(
    findings: list[Finding],
    overall_status: GuardrailOverallStatus,
    blocked_candidate_actions: list[str],
    output_control: str | None,
    requires_disclosure: bool = False,
    confidence_cap_adjustments: list[ConfidenceCapAdjustment] | None = None,
    requires_human_review: bool = False,
) -> GuardrailReport:
    return GuardrailReport(
        guardrail_report_id="gr_001",
        task_id="task_001",
        run_id="run_001",
        triggered=len(findings) > 0,
        findings=findings,
        overall_status=overall_status,
        blocked_candidate_actions=blocked_candidate_actions,
        output_control=output_control,
        requires_disclosure=requires_disclosure,
        confidence_cap_adjustments=confidence_cap_adjustments or [],
        requires_human_review=requires_human_review,
    )


def _has_insufficient_required_domain(domain_status: dict[str, str]) -> bool:
    """Check if any required domain has insufficient data."""
    return any(
        status in {"partial", "unavailable"}
        for status in domain_status.values()
    )


def _build_review_reason(triggers: list[HumanReviewTrigger]) -> str:
    return "; ".join(t.description for t in triggers)
