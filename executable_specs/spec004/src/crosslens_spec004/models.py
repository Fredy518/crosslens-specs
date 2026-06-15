"""Pydantic v2 contracts for SPEC-004 Analysis Card schema."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Domain Status ──────────────────────────────────────────────

class DomainStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


# ── Data Quality ───────────────────────────────────────────────

class DataQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


# ── Stance ─────────────────────────────────────────────────────

class Stance(str, Enum):
    POSITIVE = "positive"
    MODERATELY_POSITIVE = "moderately_positive"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    MODERATELY_NEGATIVE = "moderately_negative"
    NEGATIVE = "negative"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


# ── Time Horizon ───────────────────────────────────────────────

class TimeHorizonBucket(str, Enum):
    INTRADAY = "intraday"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    UNKNOWN = "unknown"


# ── Freshness ──────────────────────────────────────────────────

class FreshnessLevel(str, Enum):
    REAL_TIME = "real_time"
    INTRADAY = "intraday"
    DAILY = "daily"
    QUARTERLY = "quarterly"
    EVENT_BASED = "event_based"
    STATIC = "static"


class StalenessRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


# ── Constraint Export ──────────────────────────────────────────

class ExportType(str, Enum):
    METRIC = "metric"
    FACT = "fact"
    LABEL = "label"


class DeterminismLevel(str, Enum):
    COMPUTED = "computed"
    STRUCTURED = "structured"
    INTERPRETED = "interpreted"


class ConstraintExport(StrictModel):
    export_type: ExportType
    export_ref: str = Field(min_length=1)
    evidence_ref: str = Field(min_length=1)
    value_path: str | None = None       # required for metric
    determinism_level: DeterminismLevel
    can_support_hard_constraint: bool
    allowed_constraint_types: list[str]  # "hard" / "soft" / both
    fact_value: bool | None = None       # required for fact
    label_value: str | None = None       # required for label

    @model_validator(mode="after")
    def _validate_export(self) -> "ConstraintExport":
        if self.export_type is ExportType.METRIC and (
            self.value_path is None or self.value_path == ""
        ):
            raise ValueError("metric export requires value_path")
        if self.export_type is ExportType.FACT and self.fact_value is None:
            raise ValueError("fact export requires fact_value")
        if self.export_type is ExportType.LABEL and self.label_value is None:
            raise ValueError("label export requires label_value")
        if self.can_support_hard_constraint and "hard" not in self.allowed_constraint_types:
            raise ValueError(
                "can_support_hard_constraint requires 'hard' in allowed_constraint_types"
            )
        return self


# ── Data Freshness ─────────────────────────────────────────────

class DataFreshness(StrictModel):
    as_of: date
    oldest_evidence_as_of: date | None = None
    newest_evidence_as_of: date | None = None
    freshness_level: FreshnessLevel | None = None
    staleness_risk: StalenessRisk | None = None
    valid_until: date | None = None


# ── Evidence Coverage ──────────────────────────────────────────

class EvidenceCoverage(StrictModel):
    supporting_evidence_count: int = Field(ge=0)
    opposing_evidence_count: int = Field(ge=0)
    missing_required_evidence: list[str] = []


# ── Evidence Reference ─────────────────────────────────────────

class EvidenceRef(StrictModel):
    evidence_id: str = Field(min_length=1)
    evidence_type: str = ""
    description: str = ""
    determinism_level: DeterminismLevel | None = None


# ── Domain Name ────────────────────────────────────────────────

class Domain(str, Enum):
    MACRO_MESO = "macro_meso"
    FUNDAMENTALS = "fundamentals"
    COMPANY_EVENT = "company_event"
    SENTIMENT = "sentiment"
    TECHNICAL_MARKET = "technical_market"


# ── Analysis Card ──────────────────────────────────────────────

class AnalysisCard(StrictModel):
    card_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    domain: Domain
    domain_status: DomainStatus
    summary: str = ""
    stance: Stance | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence_reason: list[str] = []
    time_horizon: str = ""
    time_horizon_bucket: TimeHorizonBucket | None = None
    time_horizon_days_min: int | None = None
    time_horizon_days_max: int | None = None
    data_quality: DataQuality
    data_freshness: DataFreshness | None = None
    evidence_coverage: EvidenceCoverage | None = None
    supporting_evidence: list[EvidenceRef] = []
    opposing_evidence: list[EvidenceRef] = []
    key_findings: list[str] = []
    key_risks: list[str] = []
    invalidating_conditions: list[str] = []
    constraint_exports: list[ConstraintExport] = []
    domain_payload: dict[str, Any] = {}
    warnings: list[str] = []
    limitations: list[str] = []
    created_at: datetime

    # ── Post-card Validation Rules (SPEC-004 §41) ───────────

    @model_validator(mode="after")
    def _ban_completed_unavailable(self) -> "AnalysisCard":
        """§41 ¶7 / §5.3: completed + unavailable is forbidden."""
        if (
            self.domain_status is DomainStatus.COMPLETED
            and self.data_quality is DataQuality.UNAVAILABLE
        ):
            raise ValueError(
                "completed + unavailable is a forbidden combination"
            )
        return self

    @model_validator(mode="after")
    def _require_evidence_for_completed(self) -> "AnalysisCard":
        """§41 ¶5: completed must have at least one evidence item."""
        if self.domain_status is DomainStatus.COMPLETED:
            if not self.supporting_evidence and not self.opposing_evidence:
                raise ValueError(
                    "domain_status=completed requires at least one "
                    "supporting_evidence or opposing_evidence entry"
                )
        return self

    @model_validator(mode="after")
    def _require_opposing_for_directional_stance(self) -> "AnalysisCard":
        """§41 ¶7: directional/mixed stance requires opposing_evidence."""
        if self.stance in {
            Stance.POSITIVE,
            Stance.MODERATELY_POSITIVE,
            Stance.MIXED,
            Stance.NEGATIVE,
            Stance.MODERATELY_NEGATIVE,
        } and not self.opposing_evidence:
            raise ValueError(f"stance={self.stance} requires opposing_evidence")
        return self

    @model_validator(mode="after")
    def _warn_low_quality(self) -> "AnalysisCard":
        """§41 ¶8: data_quality=low requires warnings."""
        if self.data_quality is DataQuality.LOW and not self.warnings:
            raise ValueError("data_quality=low requires at least one warning")
        return self

    @model_validator(mode="after")
    def _domain_status_stance_constraint(self) -> "AnalysisCard":
        """§8.3: domain_status → stance hard constraints."""
        legal_stances: dict[DomainStatus, set[Stance | None]] = {
            DomainStatus.COMPLETED: {
                Stance.POSITIVE, Stance.MODERATELY_POSITIVE, Stance.NEUTRAL,
                Stance.MIXED, Stance.MODERATELY_NEGATIVE, Stance.NEGATIVE,
            },
            DomainStatus.PARTIAL: {
                Stance.POSITIVE, Stance.MODERATELY_POSITIVE, Stance.NEUTRAL,
                Stance.MIXED, Stance.MODERATELY_NEGATIVE, Stance.NEGATIVE,
                Stance.UNAVAILABLE,
            },
            DomainStatus.UNAVAILABLE: {Stance.UNAVAILABLE},
            DomainStatus.ERROR: {Stance.NOT_APPLICABLE, None},
        }
        if self.stance not in legal_stances.get(self.domain_status, set()):
            raise ValueError(
                f"stance={self.stance} is illegal for "
                f"domain_status={self.domain_status}"
            )
        return self

    @model_validator(mode="after")
    def _confidence_cap(self) -> "AnalysisCard":
        """§7.3-7.4: dual cap by data_quality + domain_status."""
        cap_by_quality = {
            DataQuality.HIGH: 0.85,
            DataQuality.MEDIUM: 0.70,
            DataQuality.LOW: 0.45,
            DataQuality.UNAVAILABLE: 0.20,
            DataQuality.UNKNOWN: 0.50,
        }
        cap_by_status = {
            DomainStatus.COMPLETED: 0.85,
            DomainStatus.PARTIAL: 0.60,
            DomainStatus.UNAVAILABLE: 0.25,
            DomainStatus.ERROR: 0.0,
        }
        max_confidence = min(
            cap_by_quality.get(self.data_quality, 1.0),
            cap_by_status.get(self.domain_status, 1.0),
        )
        if self.confidence > max_confidence:
            raise ValueError(
                f"confidence={self.confidence} exceeds cap={max_confidence} "
                f"(data_quality={self.data_quality}, domain_status={self.domain_status})"
            )
        return self

    @model_validator(mode="after")
    def _data_freshness_conditional_required(self) -> "AnalysisCard":
        """§4.3/§41 ¶11-12: data_freshness required when constraint_exports non-empty
        and domain_status ∈ {completed, partial}."""
        if (
            self.domain_status in {DomainStatus.COMPLETED, DomainStatus.PARTIAL}
            and len(self.constraint_exports) > 0
        ):
            has_hard_capable = any(
                e.can_support_hard_constraint for e in self.constraint_exports
            )
            if self.data_freshness is None:
                if has_hard_capable:
                    raise ValueError(
                        "data_freshness is required when hard-capable "
                        "constraint_exports exist and domain_status ∈ {completed, partial}"
                    )
        return self

    @model_validator(mode="after")
    def _schema_version_format(self) -> "AnalysisCard":
        """schema_version must follow SPEC-004@<semver> format."""
        if not self.schema_version.startswith("SPEC-004@"):
            raise ValueError(
                "schema_version must start with 'SPEC-004@'"
            )
        return self
