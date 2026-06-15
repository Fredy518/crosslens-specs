"""URI parsing and resolution for SPEC-003 §11 reference formats.

This module implements the parsing layer only. Full resolution (looking up
actual values in Evidence Packets, Metric Registry, and Playbook definitions)
requires runtime data and is implemented by the orchestration layer.

See docs/uri-resolution.md for the complete specification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ── Valid characters for evidence_id ──────────────────────────
_EVIDENCE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class URIError(Exception):
    """Base error for URI resolution failures."""


class URIParseError(URIError):
    """URI format is invalid (malformed, missing required parts)."""


class URIResolutionError(URIError):
    """URI is valid but the referenced entity cannot be found."""


@dataclass
class EvidenceURI:
    """Parsed evidence:// URI."""
    evidence_id: str
    value_path: str


@dataclass
class ConstraintURI:
    """Parsed constraint:// URI."""
    playbook_id: str
    version: str
    constraint_id: str


# ── URI Scheme Constants ──────────────────────────────────────

EVIDENCE_PREFIX = "evidence://"
METRIC_PREFIX = "metric://"
CONSTRAINT_PREFIX = "constraint://"

_SCHEME_MAP = {
    EVIDENCE_PREFIX: "evidence",
    METRIC_PREFIX: "metric",
    CONSTRAINT_PREFIX: "constraint",
}


# ── Public API ────────────────────────────────────────────────

def parse_evidence_uri(uri: str) -> EvidenceURI:
    """Parse evidence://<evidence_id>/<value_path> into components.

    Args:
        uri: A URI string starting with ``evidence://``.

    Returns:
        EvidenceURI with ``evidence_id`` and ``value_path`` fields.

    Raises:
        URIParseError: If the URI prefix is wrong, or any required part
            is empty, or evidence_id contains invalid characters.
    """
    if not uri.startswith(EVIDENCE_PREFIX):
        raise URIParseError(
            f"URI does not start with {EVIDENCE_PREFIX!r}: {uri!r}"
        )

    remainder = uri[len(EVIDENCE_PREFIX):]

    # Split on first "/" to separate evidence_id from value_path
    first_slash = remainder.find("/")
    if first_slash == -1:
        raise URIParseError(
            f"evidence:// URI must contain value_path: "
            f"evidence://<evidence_id>/<value_path>, got {uri!r}"
        )

    evidence_id = remainder[:first_slash]
    value_path = remainder[first_slash + 1:]

    # Validate evidence_id non-empty (including whitespace-only)
    if not evidence_id or evidence_id.isspace():
        raise URIParseError(
            f"evidence_id must be non-empty in {uri!r}"
        )

    # Validate evidence_id characters
    if not _EVIDENCE_ID_RE.match(evidence_id):
        raise URIParseError(
            f"evidence_id contains invalid characters: {evidence_id!r}"
        )

    # Validate value_path non-empty (including whitespace-only)
    if not value_path or value_path.isspace():
        raise URIParseError(
            f"value_path must be non-empty in {uri!r}"
        )

    return EvidenceURI(evidence_id=evidence_id, value_path=value_path)


def parse_metric_uri(uri: str) -> str:
    """Parse metric://<metric_id> and return metric_id.

    Args:
        uri: A URI string starting with ``metric://``.

    Returns:
        The ``metric_id`` as a string.

    Raises:
        URIParseError: If the URI prefix is wrong, metric_id is empty,
            or metric_id contains path separators.
    """
    if not uri.startswith(METRIC_PREFIX):
        raise URIParseError(
            f"URI does not start with {METRIC_PREFIX!r}: {uri!r}"
        )

    metric_id = uri[len(METRIC_PREFIX):]

    # Validate metric_id non-empty (including whitespace-only)
    if not metric_id or metric_id.isspace():
        raise URIParseError(
            f"metric_id must be non-empty in {uri!r}"
        )

    # metric:// URIs have no sub-path
    if "/" in metric_id:
        raise URIParseError(
            f"metric:// URI must not contain path separators: {uri!r}"
        )

    return metric_id


def parse_constraint_uri(uri: str) -> ConstraintURI:
    """Parse constraint://<playbook_id>/<version>/<constraint_id> into components.

    Args:
        uri: A URI string starting with ``constraint://``.

    Returns:
        ConstraintURI with ``playbook_id``, ``version``, and ``constraint_id`` fields.

    Raises:
        URIParseError: If the URI prefix is wrong, any required part
            is empty, or the number of path segments is not exactly 3.
    """
    if not uri.startswith(CONSTRAINT_PREFIX):
        raise URIParseError(
            f"URI does not start with {CONSTRAINT_PREFIX!r}: {uri!r}"
        )

    remainder = uri[len(CONSTRAINT_PREFIX):]

    # Split on "/" — expect exactly 3 parts
    parts = remainder.split("/")
    if len(parts) != 3:
        raise URIParseError(
            f"constraint:// URI must have exactly 3 path segments: "
            f"constraint://<playbook_id>/<version>/<constraint_id>, "
            f"got {len(parts)} segment(s) in {uri!r}"
        )

    playbook_id, version, constraint_id = parts[0], parts[1], parts[2]

    # Validate all parts non-empty (including whitespace-only)
    if not playbook_id or playbook_id.isspace():
        raise URIParseError(
            f"playbook_id must be non-empty in {uri!r}"
        )
    if not version or version.isspace():
        raise URIParseError(
            f"version must be non-empty in {uri!r}"
        )
    if not constraint_id or constraint_id.isspace():
        raise URIParseError(
            f"constraint_id must be non-empty in {uri!r}"
        )

    return ConstraintURI(
        playbook_id=playbook_id,
        version=version,
        constraint_id=constraint_id,
    )


def classify_uri(uri: str) -> str:
    """Return the URI scheme: ``'evidence'``, ``'metric'``, or ``'constraint'``.

    Args:
        uri: A URI string to classify.

    Returns:
        The scheme name without the ``://`` suffix.

    Raises:
        URIParseError: If the URI does not match any known scheme.
    """
    for prefix, scheme in _SCHEME_MAP.items():
        if uri.startswith(prefix):
            return scheme
    raise URIParseError(
        f"Unknown URI scheme in {uri!r}. "
        f"Expected one of: evidence://, metric://, constraint://"
    )
