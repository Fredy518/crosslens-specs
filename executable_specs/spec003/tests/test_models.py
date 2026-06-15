"""Tests for SPEC-003 core object contracts."""

from datetime import date

import pytest

from crosslens_spec003.models import (
    AnalysisDomainJob,
    AssetInfo,
    ConflictEntry,
    ConflictReport,
    ConflictSeverity,
    ContextBundle,
    ContextSource,
    DataQuality,
    DecisionCandidate,
    DeterminismLevel,
    Domain,
    DomainStatus,
    DomainStatusReason,
    EvidencePacket,
    GenerationType,
    InvestmentTask,
    PostCardValidationReport,
    Stance,
    TaskType,
    ValidationFinding,
    ValidationOverallStatus,
    ValidationSeverity,
)


# ═══════════════════════════════════════════════════════════════════
# Evidence Packet Tests
# ═══════════════════════════════════════════════════════════════════

class TestEvidencePacket:

    def test_valid_computed_evidence(self):
        ep = EvidencePacket(
            evidence_id="ev_001",
            task_id="task_001",
            domain=Domain.FUNDAMENTALS,
            as_of=date(2026, 6, 14),
            evidence_type="financial_metrics",
            generation_type=GenerationType.COMPUTED,
            determinism_level=DeterminismLevel.COMPUTED,
            can_support_hard_constraint=True,
            metrics={"revenue_growth_ttm": 0.18},
            data_quality=DataQuality.HIGH,
        )
        assert ep.confidence == 1.0  # computed default

    def test_structured_evidence_may_have_null_confidence(self):
        ep = EvidencePacket(
            evidence_id="ev_002",
            task_id="task_001",
            domain=Domain.SENTIMENT,
            evidence_type="social_sentiment_score",
            generation_type=GenerationType.STRUCTURED,
            determinism_level=DeterminismLevel.STRUCTURED,
            can_support_hard_constraint=False,
            facts=["retail_sentiment_overheated"],
            confidence=None,
        )
        assert ep.confidence is None

    def test_interpreted_cannot_support_hard(self):
        with pytest.raises(ValueError, match="Interpreted.*hard_constraint"):
            EvidencePacket(
                evidence_id="ev_003",
                task_id="task_001",
                domain=Domain.MACRO_MESO,
                evidence_type="macro_interpretation",
                generation_type=GenerationType.INTERPRETED,
                determinism_level=DeterminismLevel.INTERPRETED,
                can_support_hard_constraint=True,
                facts=["market_outlook_positive"],
            )

    def test_computed_confidence_non_null_preserved(self):
        ep = EvidencePacket(
            evidence_id="ev_004",
            task_id="task_001",
            domain=Domain.FUNDAMENTALS,
            evidence_type="valuation_metrics",
            generation_type=GenerationType.COMPUTED,
            determinism_level=DeterminismLevel.COMPUTED,
            confidence=0.85,
        )
        assert ep.confidence == 0.85

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            EvidencePacket(
                evidence_id="ev_005",
                task_id="task_001",
                domain=Domain.TECHNICAL_MARKET,
                evidence_type="price_trend",
                generation_type=GenerationType.COMPUTED,
                determinism_level=DeterminismLevel.COMPUTED,
                unknown_field="bad",
            )

    def test_evidence_type_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="evidence_type"):
            EvidencePacket(
                evidence_id="ev_006",
                task_id="task_001",
                domain=Domain.MACRO_MESO,
                evidence_type="",
                generation_type=GenerationType.COMPUTED,
                determinism_level=DeterminismLevel.COMPUTED,
            )


# ═══════════════════════════════════════════════════════════════════
# Analysis Domain Job Tests
# ═══════════════════════════════════════════════════════════════════

class TestAnalysisDomainJob:

    def test_valid_job(self):
        job = AnalysisDomainJob(
            job_id="job_001",
            task_id="task_001",
            run_id="run_001",
            domain=Domain.FUNDAMENTALS,
            evidence_refs=["ev_001", "ev_002"],
        )
        assert job.domain == Domain.FUNDAMENTALS
        assert len(job.evidence_refs) == 2

    def test_empty_evidence_refs_is_allowed(self):
        job = AnalysisDomainJob(
            job_id="job_002",
            task_id="task_001",
            run_id="run_001",
            domain=Domain.MACRO_MESO,
        )
        assert job.evidence_refs == []

    def test_reason_code_can_be_set(self):
        """reason_code allows the orchestrator to tag why a domain is error/unavailable."""
        job = AnalysisDomainJob(
            job_id="job_003",
            task_id="task_001",
            run_id="run_001",
            domain=Domain.FUNDAMENTALS,
            reason_code=DomainStatusReason.DATA_SOURCE_UNAVAILABLE,
        )
        assert job.reason_code == DomainStatusReason.DATA_SOURCE_UNAVAILABLE

    def test_reason_code_defaults_to_none(self):
        """When not set, reason_code should default to None."""
        job = AnalysisDomainJob(
            job_id="job_004",
            task_id="task_001",
            run_id="run_001",
            domain=Domain.SENTIMENT,
        )
        assert job.reason_code is None

    def test_reason_code_values_work_correctly(self):
        """Verify all DomainStatusReason values can be used."""
        for reason in DomainStatusReason:
            job = AnalysisDomainJob(
                job_id=f"job_{reason.value}",
                task_id="task_001",
                run_id="run_001",
                domain=Domain.FUNDAMENTALS,
                reason_code=reason,
            )
            assert job.reason_code == reason


# ═══════════════════════════════════════════════════════════════════
# Post-card Validation Report Tests
# ═══════════════════════════════════════════════════════════════════

class TestPostCardValidationReport:

    def test_passed_report(self):
        report = PostCardValidationReport(
            validation_report_id="vr_001",
            task_id="task_001",
            run_id="run_001",
            findings=[],
            overall_status=ValidationOverallStatus.PASSED,
        )
        assert report.overall_status == ValidationOverallStatus.PASSED

    def test_blocked_requires_blocked_cards(self):
        with pytest.raises(ValueError, match="blocked_card"):
            PostCardValidationReport(
                validation_report_id="vr_002",
                task_id="task_001",
                run_id="run_001",
                findings=[
                    ValidationFinding(
                        finding_id="f_001",
                        severity=ValidationSeverity.BLOCK,
                        card_ref="card_001",
                        description="completed + unavailable",
                    )
                ],
                overall_status=ValidationOverallStatus.BLOCKED,
                blocked_cards=[],
            )

    def test_blocked_with_cards_is_valid(self):
        report = PostCardValidationReport(
            validation_report_id="vr_003",
            task_id="task_001",
            run_id="run_001",
            findings=[
                ValidationFinding(
                    finding_id="f_001",
                    severity=ValidationSeverity.BLOCK,
                    card_ref="card_001",
                    description="completed + unavailable",
                )
            ],
            overall_status=ValidationOverallStatus.BLOCKED,
            blocked_cards=["card_001"],
        )
        assert "card_001" in report.blocked_cards


# ═══════════════════════════════════════════════════════════════════
# Conflict Report Tests
# ═══════════════════════════════════════════════════════════════════

class TestConflictReport:

    def test_valid_conflict_report(self):
        report = ConflictReport(
            conflict_report_id="cr_001",
            task_id="task_001",
            run_id="run_001",
            conflicts=[
                ConflictEntry(
                    conflict_id="c_001",
                    conflict_type="fundamentals_vs_valuation",
                    severity=ConflictSeverity.HIGH,
                    involved_domains=[Domain.FUNDAMENTALS, Domain.SENTIMENT],
                )
            ],
        )
        assert len(report.conflicts) == 1

    def test_blocking_requires_conflicts(self):
        with pytest.raises(ValueError, match="blocking_conflict"):
            ConflictReport(
                conflict_report_id="cr_002",
                task_id="task_001",
                run_id="run_001",
                has_blocking_conflict=True,
                conflicts=[],
            )

    def test_involved_domains_min_two(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ConflictEntry(
                conflict_id="c_002",
                conflict_type="test",
                severity=ConflictSeverity.LOW,
                involved_domains=[Domain.FUNDAMENTALS],
            )


# ═══════════════════════════════════════════════════════════════════
# Domain Status Canonical Tests
# ═══════════════════════════════════════════════════════════════════

class TestDomainStatusCanonical:

    def test_only_registry_values(self):
        """DomainStatus must only contain Registry-canonical values."""
        valid = {"completed", "partial", "error", "unavailable"}
        actual = {e.value for e in DomainStatus}
        assert actual == valid, f"DomainStatus={actual}, expected={valid}"

    def test_insufficient_data_is_not_domain_status(self):
        """insufficient_data is a reason_code, not a domain_status."""
        with pytest.raises((ValueError, KeyError, AttributeError)):
            DomainStatus("insufficient_data")

    def test_reason_codes_exist_separately(self):
        """DomainStatusReason provides granularity without splitting the enum."""
        assert DomainStatusReason.INSUFFICIENT_DATA.value == "insufficient_data"
        assert DomainStatusReason.SKIPPED_BY_CONFIG.value == "skipped_by_config"


# ═══════════════════════════════════════════════════════════════════
# Decision Candidate Tests
# ═══════════════════════════════════════════════════════════════════

class TestDecisionCandidate:

    def test_valid_candidate(self):
        dc = DecisionCandidate(
            decision_candidate_id="dc_001",
            task_id="task_001",
            run_id="run_001",
            suggested_action="hold",
            allowed_actions=["hold", "wait", "add_to_watchlist"],
            confidence=0.58,
            key_supporting_reasons=["fundamentals positive"],
            key_opposing_reasons=["valuation stretched"],
        )
        assert dc.suggested_action == "hold"

    def test_suggested_action_must_be_in_allowed(self):
        with pytest.raises(ValueError, match="suggested_action"):
            DecisionCandidate(
                decision_candidate_id="dc_002",
                task_id="task_001",
                run_id="run_001",
                suggested_action="buy",
                allowed_actions=["hold", "wait"],
                confidence=0.5,
            )

    def test_block_output_not_in_allowed(self):
        with pytest.raises(ValueError, match="block_output"):
            DecisionCandidate(
                decision_candidate_id="dc_003",
                task_id="task_001",
                run_id="run_001",
                suggested_action="hold",
                allowed_actions=["block_output", "hold"],
                confidence=0.5,
            )

    def test_output_control_block_output_no_suggested_action(self):
        """When block_output is active, no suggested action should be present."""
        # model_validator says: if output_control=block_output AND suggested_action → error
        with pytest.raises(ValueError, match="output_control.*block_output"):
            DecisionCandidate(
                decision_candidate_id="dc_004",
                task_id="task_001",
                run_id="run_001",
                suggested_action="hold",
                allowed_actions=[],
                confidence=0.0,
                output_control="block_output",
            )


# ═══════════════════════════════════════════════════════════════════
# Stance Canonical Tests
# ═══════════════════════════════════════════════════════════════════

class TestStanceCanonical:

    def test_stance_values_match_registry(self):
        expected = {
            "positive", "moderately_positive", "neutral", "mixed",
            "moderately_negative", "negative", "unavailable", "not_applicable",
        }
        actual = {e.value for e in Stance}
        assert actual == expected

    def test_insufficient_data_is_not_stance(self):
        with pytest.raises((ValueError, KeyError, AttributeError)):
            Stance("insufficient_data")


# ═══════════════════════════════════════════════════════════════════
# Context Bundle Tests (§6.2)
# ═══════════════════════════════════════════════════════════════════

class TestContextBundle:

    def test_valid_context_bundle(self):
        source = ContextSource(
            source_id="src_001",
            source_type="market_data",
            source_name="Bloomberg RTH Quote",
            as_of=date(2026, 6, 14),
            data_quality=DataQuality.HIGH,
            payload={"price": 150.25, "volume": 1_200_000},
        )
        bundle = ContextBundle(
            context_bundle_id="cb_001",
            task_id="task_001",
            run_id="run_001",
            sources=[source],
        )
        assert bundle.context_bundle_id == "cb_001"
        assert len(bundle.sources) == 1
        assert bundle.sources[0].source_id == "src_001"
        assert bundle.sources[0].payload["price"] == 150.25

    def test_context_bundle_empty_sources_allowed(self):
        """Empty sources list is OK — MVP may run with sources populated incrementally."""
        bundle = ContextBundle(
            context_bundle_id="cb_002",
            task_id="task_001",
            run_id="run_001",
        )
        assert bundle.sources == []
        assert bundle.data_quality_overall == DataQuality.UNKNOWN

    def test_context_bundle_with_multiple_sources(self):
        src1 = ContextSource(
            source_id="src_001",
            source_type="market_data",
            source_name="Bloomberg RTH",
            data_quality=DataQuality.HIGH,
            payload={"price": 150.25},
        )
        src2 = ContextSource(
            source_id="src_002",
            source_type="news",
            source_name="Reuters Feed",
            data_quality=DataQuality.MEDIUM,
            payload={"headline": "Earnings beat expectations"},
        )
        src3 = ContextSource(
            source_id="src_003",
            source_type="financial_report",
            source_name="10-K Filing",
            as_of=date(2026, 3, 31),
            data_quality=DataQuality.HIGH,
            payload={"revenue": 5_200_000_000},
        )
        bundle = ContextBundle(
            context_bundle_id="cb_003",
            task_id="task_001",
            run_id="run_001",
            sources=[src1, src2, src3],
            data_quality_overall=DataQuality.MEDIUM,
        )
        assert len(bundle.sources) == 3
        assert bundle.sources[0].source_type == "market_data"
        assert bundle.sources[1].source_type == "news"
        assert bundle.sources[2].source_type == "financial_report"
        assert bundle.data_quality_overall == DataQuality.MEDIUM

    def test_context_source_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            ContextSource(
                source_id="src_001",
                source_type="market_data",
                unknown_field="bad",
            )

    def test_context_bundle_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            ContextBundle(
                context_bundle_id="cb_004",
                task_id="task_001",
                run_id="run_001",
                unknown_field="bad",
            )


# ═══════════════════════════════════════════════════════════════════
# Investment Task Tests
# ═══════════════════════════════════════════════════════════════════

class TestInvestmentTask:

    def test_valid_investment_task(self):
        task = InvestmentTask(
            task_id="task_001",
            task_type=TaskType.SINGLE_STOCK_BUY_DECISION,
            asset=AssetInfo(
                symbol="AAPL",
                asset_type="stock",
                market="US",
            ),
            user_intent="whether_to_buy",
            time_horizon="6m",
            playbook_id="pb_001",
            depth="standard",
            risk_preference="medium",
            uses_user_private_data=False,
            user_private_data_types=[],
        )
        assert task.task_id == "task_001"
        assert task.task_type == TaskType.SINGLE_STOCK_BUY_DECISION
        assert task.asset.symbol == "AAPL"
        assert task.playbook_id == "pb_001"
        assert task.depth == "standard"
        assert task.risk_preference == "medium"

    def test_investment_task_symbol_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises((ValueError, ValidationError)):
            InvestmentTask(
                task_id="task_002",
                task_type=TaskType.SINGLE_STOCK_BUY_DECISION,
                asset=AssetInfo(
                    symbol="",
                    asset_type="stock",
                    market="US",
                ),
                playbook_id="pb_002",
            )

    def test_investment_task_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            InvestmentTask(
                task_id="task_003",
                task_type=TaskType.SINGLE_STOCK_BUY_DECISION,
                asset=AssetInfo(
                    symbol="AAPL",
                    asset_type="stock",
                    market="US",
                ),
                playbook_id="pb_003",
                unknown_field="bad",
            )

    def test_investment_task_nested_asset_validation(self):
        with pytest.raises(ValueError, match="asset.symbol must be non-empty"):
            InvestmentTask(
                task_id="task_004",
                task_type=TaskType.SINGLE_STOCK_BUY_DECISION,
                asset=AssetInfo(
                    symbol="   ",  # whitespace only
                    asset_type="stock",
                    market="US",
                ),
                playbook_id="pb_004",
            )

    def test_investment_task_playbook_id_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises((ValueError, ValidationError)):
            InvestmentTask(
                task_id="task_005",
                task_type=TaskType.SINGLE_STOCK_BUY_DECISION,
                asset=AssetInfo(
                    symbol="AAPL",
                    asset_type="stock",
                    market="US",
                ),
                playbook_id="",
            )
