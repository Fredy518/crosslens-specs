"""
crosslens_spec004 — Executable contracts for SPEC-004: Analysis Card Schema.

Normative definitions for:
- DomainStatus (completed, partial, insufficient_data, failed, skipped)
- DataQuality (high, medium, low, unavailable, unknown)
- Stance (positive, moderately_positive, neutral, mixed, moderately_negative, negative, insufficient_data, not_applicable)
- TimeHorizonBucket (intraday, short_term, medium_term, long_term, unknown)
- FreshnessLevel (real_time, intraday, daily, quarterly, event_based, static)
- StalenessRisk (low, medium, high, unknown)
- ConstraintExport (metric / fact / label)
- AnalysisCard — the core domain output object
"""
