"""Pydantic v2 contracts for SPEC-009 Governance layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Guardrail ──────────────────────────────────────────────────

class GuardrailSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class GuardrailOverallStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_CONSTRAINTS = "passed_with_constraints"
    REQUIRES_MODIFICATION = "requires_modification"
    BLOCKED = "blocked"


class Finding(StrictModel):
    guardrail_id: str = Field(min_length=1)
    severity: GuardrailSeverity
    action: str = Field(min_length=1)
    description: str = ""
    evidence_refs: list[str] = []


class ConfidenceCapAdjustment(StrictModel):
    source: str = Field(min_length=1)
    reason: str = ""
    cap_value: float = Field(ge=0.0, le=1.0)


class GuardrailReport(StrictModel):
    guardrail_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    triggered: bool
    findings: list[Finding] = []
    overall_status: GuardrailOverallStatus
    blocked_candidate_actions: list[str] = []
    output_control: str | None = None  # "block_output" | None
    requires_disclosure: bool = False
    confidence_cap_adjustments: list[ConfidenceCapAdjustment] = []
    requires_human_review: bool

    @model_validator(mode="after")
    def _output_control_is_not_allowed_action(self) -> "GuardrailReport":
        """output_control=block_output must not appear in blocked_candidate_actions."""
        if "block_output" in self.blocked_candidate_actions:
            raise ValueError(
                "block_output is a governance control flag, not an AllowedAction. "
                "Use output_control='block_output' instead."
            )
        return self


# ── Evaluator ──────────────────────────────────────────────────

class EvaluatorDimension(str, Enum):
    EVIDENCE_QUALITY = "evidence_quality"
    REASONING_COHERENCE = "reasoning_coherence"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    COMPLETENESS = "completeness"


class EvaluatorSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class OverallQuality(str, Enum):
    ACCEPTABLE = "acceptable"
    ACCEPTABLE_WITH_CAVEATS = "acceptable_with_caveats"
    NEEDS_REVISION = "needs_revision"


class EvaluationFinding(StrictModel):
    dimension: EvaluatorDimension
    severity: EvaluatorSeverity
    description: str = ""
    recommended_action: str = ""
    details: list[str] | None = None


class EvaluationReport(StrictModel):
    evaluation_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    findings: list[EvaluationFinding] = []
    quality_flags: list[str] = []
    overall_quality: OverallQuality
    confidence_cap_adjustments: list[ConfidenceCapAdjustment] = []


# ── Human Review ───────────────────────────────────────────────

class HumanReviewTriggerType(str, Enum):
    GUARDRAIL_BLOCK_OR_CRITICAL = "guardrail_block_or_critical"
    BLOCKING_CONFLICT = "blocking_conflict"
    PLAYBOOK_REQUIRES_REVIEW = "playbook_requires_review"
    CONFIDENCE_CAP_BELOW_THRESHOLD = "confidence_cap_below_threshold"
    MACRO_PARTIAL_WITH_CONFLICT = "macro_partial_with_conflict"
    FUNDAMENTALS_UNAVAILABLE = "fundamentals_unavailable"


class HumanReviewTrigger(StrictModel):
    source: str = Field(min_length=1)
    source_ref: str = ""
    trigger_type: HumanReviewTriggerType
    description: str = ""


# ── Confidence Cap Reason ──────────────────────────────────────

class ConfidenceCapReason(StrictModel):
    source_type: str = Field(min_length=1)  # guardrail / evaluator / preference
    source_ref: str = ""
    reason: str = ""
    effect: str = ""


# ── Reason Entry ───────────────────────────────────────────────

class ReasonEntry(StrictModel):
    source: str = Field(min_length=1)
    action: str = ""
    detail: str = ""


# ── Contamination Result ───────────────────────────────────────

class ContaminationLevel(str, Enum):
    CLEAN = "clean"
    POTENTIALLY_CONTAMINATED = "potentially_contaminated"
    CONTAMINATED = "contaminated"
    UNKNOWN = "unknown"


class ContaminationResult(StrictModel):
    contamination_level: ContaminationLevel
    contamination_path: list[str] = []
    reason: str = ""


class ContaminationFinding(StrictModel):
    evidence_id: str = Field(min_length=1)
    contamination_level: ContaminationLevel
    contamination_path: list[str] = []
    reason: str = ""


# ── Resolved Decision Bounds ───────────────────────────────────

class ResolvedDecisionBounds(StrictModel):
    resolved_decision_bounds_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    allowed_actions: list[str] = []
    blocked_candidate_actions: list[str] = []
    output_control: str | None = None
    requires_human_review: bool
    human_review_triggers: list[HumanReviewTrigger] = []
    confidence_cap: float = Field(ge=0.0, le=1.0)
    confidence_cap_reason: list[ConfidenceCapReason] = []
    applied_rules: list[str] = []
    reasoning: list[ReasonEntry] = []
    contamination_findings: list[ContaminationFinding] = []

    @model_validator(mode="after")
    def _output_control_not_in_allowed_or_blocked(self) -> "ResolvedDecisionBounds":
        if self.output_control == "block_output":
            if "block_output" in self.allowed_actions:
                raise ValueError("block_output must not appear in allowed_actions")
            if "block_output" in self.blocked_candidate_actions:
                raise ValueError("block_output must not appear in blocked_candidate_actions")
        return self

    @model_validator(mode="after")
    def _forbidden_combinations(self) -> "ResolvedDecisionBounds":
        """§8.2: Hard-forbidden action combinations."""
        forbidden = (
            frozenset({"buy", "avoid"}),
            frozenset({"add_position", "avoid"}),
            frozenset({"buy", "reduce"}),
            frozenset({"add_position", "reduce"}),
        )
        intersection = set(self.allowed_actions)
        for combo in forbidden:
            if combo.issubset(intersection):
                raise ValueError(
                    f"forbidden combination found: {set(combo)} in allowed_actions"
                )
        return self

    @model_validator(mode="after")
    def _no_forbidden_actions_in_allowed(self) -> "ResolvedDecisionBounds":
        """block_output is not an AllowedAction and must never appear in allowed_actions."""
        forbidden_values = {"block_output", "strong_buy", "strong_sell", "sell", "reduce_position"}
        intersection = set(self.allowed_actions) & forbidden_values
        if intersection:
            raise ValueError(
                f"forbidden values in allowed_actions: {intersection}"
            )
        return self

    @model_validator(mode="after")
    def _requires_human_review_consistent(self) -> "ResolvedDecisionBounds":
        if self.requires_human_review and len(self.human_review_triggers) == 0:
            raise ValueError(
                "requires_human_review=true requires at least one human_review_trigger"
            )
        return self


# ── Route Decision ─────────────────────────────────────────────

class RouteAction(str, Enum):
    PROCEED_TO_CANDIDATE = "proceed_to_candidate"
    BLOCK_CANDIDATE = "block_candidate"


class RouteDecision(StrictModel):
    action: RouteAction
    user_visible_status: str | None = None
    user_visible_reason: str = ""
    next_step: str = ""
