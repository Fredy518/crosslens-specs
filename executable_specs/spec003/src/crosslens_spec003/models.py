"""Pydantic v2 contracts for SPEC-003: Evidence Packet & Core Objects."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Type Aliases (§6.1) ───────────────────────────────────────

RiskPreference = Literal["low", "medium", "high"]
Depth = Literal["quick", "standard", "deep"]


# ── Task Types (§6.1, SPEC-002 routing decision tree) ─────────

class TaskType(str, Enum):
    SINGLE_STOCK_BUY_DECISION = "single_stock_buy_decision"
    SINGLE_STOCK_HOLD_REVIEW = "single_stock_hold_review"
    SINGLE_STOCK_WATCHLIST_REVIEW = "single_stock_watchlist_review"
    INDUSTRY_SCAN = "industry_scan"
    POSITION_REVIEW = "position_review"
    RESEARCH_NOTE_TO_DECISION = "research_note_to_decision"


# ── Asset Info (§6.1) ─────────────────────────────────────────

class AssetInfo(StrictModel):
    symbol: str = Field(min_length=1)
    asset_type: str = ""          # "stock", "etf", "bond", etc.
    market: str = ""              # "US", "HK", "CN", etc.


# ── Investment Task (§6.1) ────────────────────────────────────

class InvestmentTask(StrictModel):
    task_id: str = Field(min_length=1)
    task_type: TaskType
    asset: AssetInfo
    user_intent: str = ""                  # "whether_to_buy", "whether_to_hold", etc.
    time_horizon: str = ""
    playbook_id: str = Field(min_length=1)
    depth: str = "standard"                # Depth literal
    risk_preference: str = "medium"        # RiskPreference literal
    uses_user_private_data: bool = False
    user_private_data_types: list[str] = []
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _symbol_not_empty(self) -> "InvestmentTask":
        if not self.asset.symbol or len(self.asset.symbol.strip()) == 0:
            raise ValueError("asset.symbol must be non-empty")
        return self

    @model_validator(mode="after")
    def _playbook_id_not_empty(self) -> "InvestmentTask":
        if not self.playbook_id or len(self.playbook_id.strip()) == 0:
            raise ValueError("playbook_id must be non-empty and cannot be whitespace")
        return self

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
    evidence_type: str = Field(min_length=1)
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


# ── Context Bundle (§6.2) ─────────────────────────────────────

class ContextSource(StrictModel):
    """A single data source within a Context Bundle.

    MVP minimal shape — full Context Bundle source taxonomy defined by later SPEC.
    """
    source_id: str = Field(min_length=1)
    source_type: str = ""           # e.g. "market_data", "financial_report", "news", "user_private"
    source_name: str = ""
    as_of: date | None = None
    data_quality: DataQuality = DataQuality.UNKNOWN
    payload: dict[str, Any] = {}    # source-specific content; MVP uses Any


class ContextBundle(StrictModel):
    """Execution context collection — raw material for Evidence Packet generation.

    MVP minimal shape — full Context Bundle design defined by later SPEC.
    """
    context_bundle_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    sources: list[ContextSource] = []  # may be empty in MVP — sources populated incrementally
    created_at: datetime | None = None
    data_quality_overall: DataQuality = DataQuality.UNKNOWN


# ── Analysis Domain Job (§8) ──────────────────────────────────

class AnalysisDomainJob(StrictModel):
    """Orchestrator → Domain dispatch work order."""
    job_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    domain: Domain
    task: dict[str, Any] = {}                       # Investment Task snapshot
    context_bundle_ref: str = ""                     # ref to Context Bundle
    evidence_refs: list[str] = []                    # may be empty for domains that generate their own evidence (e.g., sentiment from raw social data)
    constraints: list[dict[str, Any]] = []            # Playbook constraints to check
    run_config: dict[str, Any] = {}                  # RunConfig snapshot
    reason_code: DomainStatusReason | None = None    # set by orchestrator when domain produces error/unavailable status
    created_at: datetime | None = None


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
    resolved_decision_bounds_id: str = ""
    playbook_evaluation_report_id: str | None = None
    guardrail_report_id: str | None = None
    validation_report_refs: list[str] = []
    conflict_report_refs: list[str] = []
    suggested_action: str = Field(min_length=1)
    allowed_actions: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_cap: float = Field(ge=0.0, le=1.0, default=1.0)
    key_supporting_reasons: list[str] = []
    key_opposing_reasons: list[str] = []
    next_steps: list[str] = []
    action_selection_reason: str = ""
    requires_human_review: bool = False
    output_control: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _allowed_actions_not_empty(self) -> "DecisionCandidate":
        """P0: empty allowed_actions means no bounds — cannot generate candidate."""
        if not self.allowed_actions:
            raise ValueError(
                "DecisionCandidate requires non-empty allowed_actions. "
                "Empty bounds should route to analysis_incomplete notice, not a candidate."
            )
        return self

    @model_validator(mode="after")
    def _suggested_action_in_allowed(self) -> "DecisionCandidate":
        if self.suggested_action not in self.allowed_actions:
            raise ValueError(
                f"suggested_action={self.suggested_action} "
                f"must be in allowed_actions={self.allowed_actions}"
            )
        return self

    @model_validator(mode="after")
    def _confidence_le_cap(self) -> "DecisionCandidate":
        """P0: confidence must not exceed confidence_cap (§17.4)."""
        if self.confidence > self.confidence_cap:
            raise ValueError(
                f"confidence={self.confidence} must not exceed "
                f"confidence_cap={self.confidence_cap}"
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
