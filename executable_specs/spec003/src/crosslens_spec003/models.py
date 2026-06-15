"""Pydantic v2 contracts for SPEC-003: Evidence Packet & Core Objects."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Enums (§6.3, §6.5, §7) ────────────────────────────────────

class GenerationType(str, Enum):
    COMPUTED = "computed"
    STRUCTURED = "structured"
    INTERPRETED = "interpreted"


class DeterminismLevel(str, Enum):
    COMPUTED = "computed"
    STRUCTURED = "structured"
    INTERPRETED = "interpreted"
    LOW = "low"
    UNKNOWN = "unknown"


class Domain(str, Enum):
    MACRO_MESO = "macro_meso"
    FUNDAMENTALS = "fundamentals"
    COMPANY_EVENT = "company_event"
    SENTIMENT = "sentiment"
    TECHNICAL_MARKET = "technical_market"


class DataQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class DomainStatus(str, Enum):
    """Registry canonical: completed / partial / error / unavailable."""
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class Stance(str, Enum):
    POSITIVE = "positive"
    MODERATELY_POSITIVE = "moderately_positive"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    MODERATELY_NEGATIVE = "moderately_negative"
    NEGATIVE = "negative"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


# ── Reason Codes (explain domain_status without splitting it) ──

class DomainStatusReason(str, Enum):
    INSUFFICIENT_DATA = "insufficient_data"
    SKIPPED_BY_CONFIG = "skipped_by_config"
    EXECUTION_FAILURE = "execution_failure"
    DATA_SOURCE_UNAVAILABLE = "data_source_unavailable"


# ── Validation Severity ────────────────────────────────────────

class ValidationSeverity(str, Enum):
    BLOCK = "block"
    FLAG = "flag"
    NOTE = "note"


# ── Validation Overall Status ──────────────────────────────────

class ValidationOverallStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_FLAGS = "passed_with_flags"
    BLOCKED = "blocked"
    ERROR = "error"
    SKIPPED = "skipped"


# ── Conflict Severity ─────────────────────────────────────────

class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Evidence Packet (§6.5) ────────────────────────────────────

class EvidencePacket(StrictModel):
    """Structured evidence object — the most consumed data object in the pipeline."""
    evidence_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    domain: Domain
    source_type: str = ""
    source_name: str = ""
    as_of: date | None = None
    evidence_type: str = ""
    generation_type: GenerationType
    determinism_level: DeterminismLevel
    can_support_hard_constraint: bool = False
    metrics: dict[str, float | bool] = {}
    facts: list[str] = []
    labels: dict[str, str] = {}
    signal: str = ""
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    data_quality: DataQuality = DataQuality.UNKNOWN
    time_horizon: str = ""
    limitations: list[str] = []

    @model_validator(mode="after")
    def _interpreted_cannot_support_hard(self) -> "EvidencePacket":
        if self.generation_type is GenerationType.INTERPRETED and self.can_support_hard_constraint:
            raise ValueError(
                "Interpreted Evidence must not set can_support_hard_constraint=true"
            )
        return self

    @model_validator(mode="after")
    def _computed_confidence_defaults(self) -> "EvidencePacket":
        if self.generation_type is GenerationType.COMPUTED and self.confidence is None:
            # defaults to 1.0 per SPEC-005 §4.4.1
            object.__setattr__(self, "confidence", 1.0)
        return self


# ── Analysis Domain Job (§8) ──────────────────────────────────

class AnalysisDomainJob(StrictModel):
    """Orchestrator → Domain dispatch work order."""
    job_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    domain: Domain
    task: dict[str, Any] = {}                       # Investment Task snapshot
    context_bundle_ref: str = ""                     # ref to Context Bundle
    evidence_refs: list[str] = []                    # domain-relevant Evidence Packet IDs
    constraints: list[dict[str, Any]] = []            # Playbook constraints to check
    run_config: dict[str, Any] = {}                  # RunConfig snapshot
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _evidence_refs_not_empty(self) -> "AnalysisDomainJob":
        # soft: warn but don't block — some domains may run without evidence
        return self


# ── Post-card Validation Report (§13) ─────────────────────────

class ValidationFinding(StrictModel):
    finding_id: str = Field(min_length=1)
    severity: ValidationSeverity
    card_ref: str = ""
    rule_ref: str = ""                               # §41 rule number or id
    description: str = ""
    evidence_refs: list[str] = []


class PostCardValidationReport(StrictModel):
    """Quality check results for Analysis Cards (§13)."""
    validation_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage: str = "post_card"
    findings: list[ValidationFinding] = []
    overall_status: ValidationOverallStatus
    blocked_cards: list[str] = []                    # card_ids that are blocked
    flagged_cards: list[str] = []

    @model_validator(mode="after")
    def _blocked_status_consistent(self) -> "PostCardValidationReport":
        if self.overall_status is ValidationOverallStatus.BLOCKED and not self.blocked_cards:
            raise ValueError(
                "overall_status=blocked requires at least one blocked_card"
            )
        return self


# ── Conflict Report (§14) ─────────────────────────────────────

class ConflictEntry(StrictModel):
    conflict_id: str = Field(min_length=1)
    conflict_type: str = Field(min_length=1)          # e.g. fundamentals_vs_valuation
    severity: ConflictSeverity
    involved_domains: list[Domain] = Field(min_length=2, max_length=5)
    involved_card_refs: list[str] = []
    evidence_refs: list[str] = []
    description: str = ""
    decision_impact: str = ""                         # e.g. lower_confidence, require_human_review
    resolution: str = ""                              # auto resolution if any


class ConflictReport(StrictModel):
    """Cross-domain conflict record (§14)."""
    conflict_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    conflicts: list[ConflictEntry] = []
    has_blocking_conflict: bool = False
    deweighted_card_refs: list[str] = []
    deweight_reason: str = ""

    @model_validator(mode="after")
    def _blocking_requires_conflict(self) -> "ConflictReport":
        if self.has_blocking_conflict and not self.conflicts:
            raise ValueError(
                "has_blocking_conflict=true requires at least one conflict entry"
            )
        return self


# ── Decision Candidate (§18) ──────────────────────────────────

class DecisionCandidate(StrictModel):
    """Final decision proposal from the system (§18)."""
    decision_candidate_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)
    allowed_actions: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_cap: float = Field(ge=0.0, le=1.0, default=1.0)
    key_supporting_reasons: list[str] = []
    key_opposing_reasons: list[str] = []
    action_selection_reason: str = ""
    requires_human_review: bool = False
    output_control: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _suggested_action_in_allowed(self) -> "DecisionCandidate":
        if self.allowed_actions and self.suggested_action not in self.allowed_actions:
            raise ValueError(
                f"suggested_action={self.suggested_action} "
                f"must be in allowed_actions={self.allowed_actions}"
            )
        return self

    @model_validator(mode="after")
    def _block_output_not_in_actions(self) -> "DecisionCandidate":
        if "block_output" in self.allowed_actions:
            raise ValueError(
                "block_output is a governance control flag, not an AllowedAction"
            )
        if self.output_control == "block_output" and self.suggested_action:
            raise ValueError(
                "output_control=block_output: suggested_action should be empty"
            )
        return self
