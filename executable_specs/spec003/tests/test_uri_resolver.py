"""Tests for URI parsing and resolution (SPEC-003 §11)."""

import pytest

from crosslens_spec003.uri_resolver import (
    ConstraintURI,
    EvidenceURI,
    URIParseError,
    classify_uri,
    parse_constraint_uri,
    parse_evidence_uri,
    parse_metric_uri,
)


class TestParseEvidenceURI:

    def test_valid_simple_path(self):
        uri = "evidence://ev_001/metrics.revenue_growth_ttm"
        result = parse_evidence_uri(uri)
        assert isinstance(result, EvidenceURI)
        assert result.evidence_id == "ev_001"
        assert result.value_path == "metrics.revenue_growth_ttm"

    def test_valid_facts_index_path(self):
        uri = "evidence://ev_001/facts.0"
        result = parse_evidence_uri(uri)
        assert result.evidence_id == "ev_001"
        assert result.value_path == "facts.0"

    def test_no_value_path_raises_error(self):
        """evidence://ev_001 without a value path raises URIParseError."""
        with pytest.raises(URIParseError, match="value_path"):
            parse_evidence_uri("evidence://ev_001")

    def test_invalid_prefix_raises_error(self):
        """Non-evidence scheme raises URIParseError."""
        with pytest.raises(URIParseError, match="does not start with"):
            parse_evidence_uri("http://example.com")

    def test_empty_evidence_id_raises_error(self):
        """evidence:///metrics.x has empty evidence_id."""
        with pytest.raises(URIParseError, match="evidence_id must be non-empty"):
            parse_evidence_uri("evidence:///metrics.x")

    def test_nested_path(self):
        """Deeply nested dot-path should parse correctly."""
        uri = "evidence://ev_001/metrics.a.b.c"
        result = parse_evidence_uri(uri)
        assert result.evidence_id == "ev_001"
        assert result.value_path == "metrics.a.b.c"

    def test_whitespace_only_evidence_id(self):
        """Whitespace-only evidence_id raises URIParseError."""
        with pytest.raises(URIParseError, match="evidence_id must be non-empty"):
            parse_evidence_uri("evidence:// /metrics.x")

    def test_whitespace_only_value_path(self):
        """Whitespace-only value_path raises URIParseError."""
        with pytest.raises(URIParseError, match="value_path must be non-empty"):
            parse_evidence_uri("evidence://ev_001/ ")

    def test_invalid_evidence_id_characters(self):
        """evidence_id with invalid characters raises URIParseError."""
        with pytest.raises(URIParseError, match="invalid characters"):
            parse_evidence_uri("evidence://ev@bogus!/metrics.x")

    def test_evidence_id_with_hyphens_and_underscores(self):
        """Hyphens and underscores in evidence_id are valid."""
        uri = "evidence://ev-financial_001/metrics.rev"
        result = parse_evidence_uri(uri)
        assert result.evidence_id == "ev-financial_001"
        assert result.value_path == "metrics.rev"

    def test_value_path_with_array_indices(self):
        """Array index notation in value_path is preserved as-is."""
        uri = "evidence://ev_001/facts.0.subfield"
        result = parse_evidence_uri(uri)
        assert result.value_path == "facts.0.subfield"

    def test_value_path_with_single_segment(self):
        """Single-segment value_path (no dots) is valid."""
        uri = "evidence://ev_001/signal"
        result = parse_evidence_uri(uri)
        assert result.value_path == "signal"


class TestParseMetricURI:

    def test_valid_metric_uri(self):
        uri = "metric://revenue_growth_ttm"
        result = parse_metric_uri(uri)
        assert result == "revenue_growth_ttm"

    def test_valid_metric_with_underscores(self):
        uri = "metric://industry_median_revenue_growth_ttm"
        result = parse_metric_uri(uri)
        assert result == "industry_median_revenue_growth_ttm"

    def test_empty_metric_id_raises_error(self):
        """metric:// with no id raises URIParseError."""
        with pytest.raises(URIParseError, match="metric_id must be non-empty"):
            parse_metric_uri("metric://")

    def test_invalid_prefix_raises_error(self):
        """Non-metric scheme raises URIParseError."""
        with pytest.raises(URIParseError, match="does not start with"):
            parse_metric_uri("http://example.com")

    def test_path_separator_raises_error(self):
        """metric:// URI with a path separator raises URIParseError."""
        with pytest.raises(URIParseError, match="path separators"):
            parse_metric_uri("metric://a/b")

    def test_whitespace_only_metric_id(self):
        """Whitespace-only metric_id raises URIParseError."""
        with pytest.raises(URIParseError, match="metric_id must be non-empty"):
            parse_metric_uri("metric://   ")

    def test_metric_id_with_numbers(self):
        uri = "metric://rsi_14d"
        result = parse_metric_uri(uri)
        assert result == "rsi_14d"


class TestParseConstraintURI:

    def test_valid_constraint_uri(self):
        uri = "constraint://capital_cycle_fundamental_playbook/0.1.0/growth_001"
        result = parse_constraint_uri(uri)
        assert isinstance(result, ConstraintURI)
        assert result.playbook_id == "capital_cycle_fundamental_playbook"
        assert result.version == "0.1.0"
        assert result.constraint_id == "growth_001"

    def test_too_few_parts_raises_error(self):
        """Less than 3 path segments raises URIParseError."""
        with pytest.raises(URIParseError, match="exactly 3 path segments"):
            parse_constraint_uri("constraint://playbook/version")

    def test_too_many_parts_raises_error(self):
        """More than 3 path segments raises URIParseError."""
        with pytest.raises(URIParseError, match="exactly 3 path segments"):
            parse_constraint_uri("constraint://pb/0.1.0/c001/extra")

    def test_empty_playbook_id_raises_error(self):
        """Empty playbook_id (constraint:///0.1.0/c001) raises URIParseError."""
        with pytest.raises(URIParseError, match="playbook_id must be non-empty"):
            parse_constraint_uri("constraint:///0.1.0/c001")

    def test_empty_version_raises_error(self):
        with pytest.raises(URIParseError, match="version must be non-empty"):
            parse_constraint_uri("constraint://pb//c001")

    def test_empty_constraint_id_raises_error(self):
        with pytest.raises(URIParseError, match="constraint_id must be non-empty"):
            parse_constraint_uri("constraint://pb/0.1.0/")

    def test_whitespace_only_playbook_id(self):
        with pytest.raises(URIParseError, match="playbook_id must be non-empty"):
            parse_constraint_uri("constraint:// /0.1.0/c001")

    def test_whitespace_only_version(self):
        with pytest.raises(URIParseError, match="version must be non-empty"):
            parse_constraint_uri("constraint://pb/ /c001")

    def test_whitespace_only_constraint_id(self):
        with pytest.raises(URIParseError, match="constraint_id must be non-empty"):
            parse_constraint_uri("constraint://pb/0.1.0/ ")

    def test_invalid_prefix_raises_error(self):
        """Non-constraint scheme raises URIParseError."""
        with pytest.raises(URIParseError, match="does not start with"):
            parse_constraint_uri("http://example.com")

    def test_valid_semver_version_with_prerelease(self):
        """Semver-like versions with prerelease tags should work."""
        uri = "constraint://pb/0.2.0-alpha/c001"
        result = parse_constraint_uri(uri)
        assert result.version == "0.2.0-alpha"


class TestClassifyURI:

    def test_classify_evidence(self):
        assert classify_uri("evidence://ev_001/metrics.x") == "evidence"

    def test_classify_metric(self):
        assert classify_uri("metric://revenue_growth_ttm") == "metric"

    def test_classify_constraint(self):
        assert classify_uri(
            "constraint://pb/0.1.0/c001"
        ) == "constraint"

    def test_classify_unknown_raises_error(self):
        """Unknown scheme raises URIParseError."""
        with pytest.raises(URIParseError, match="Unknown URI scheme"):
            classify_uri("http://example.com")

    def test_classify_empty_string(self):
        """Empty string is an unknown scheme."""
        with pytest.raises(URIParseError, match="Unknown URI scheme"):
            classify_uri("")

    def test_classify_near_miss(self):
        """A URI that partially matches but not exactly."""
        with pytest.raises(URIParseError, match="Unknown URI scheme"):
            classify_uri("evidences://ev_001/x")


class TestRoundTrip:

    def test_evidence_uri_round_trip(self):
        """Parsed evidence URI reconstructs to the original components."""
        original = "evidence://ev_financial_001/metrics.revenue_growth_ttm"
        parsed = parse_evidence_uri(original)
        reconstructed = f"evidence://{parsed.evidence_id}/{parsed.value_path}"
        assert reconstructed == original

    def test_constraint_uri_round_trip(self):
        """Parsed constraint URI reconstructs to the original components."""
        original = "constraint://capital_cycle_fundamental_playbook/0.1.0/growth_001"
        parsed = parse_constraint_uri(original)
        reconstructed = (
            f"constraint://{parsed.playbook_id}/"
            f"{parsed.version}/{parsed.constraint_id}"
        )
        assert reconstructed == original
