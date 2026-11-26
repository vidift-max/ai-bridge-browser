"""Offline, allowlist-based collector for staging deployment evidence.

Only approved metadata fields are copied into the report. Unknown fields (which
may include secrets) are never echoed. This module performs no I/O or probing.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from server.staging_deployment_contract import (
    StagingDeploymentEvidence,
    evaluate_staging_deployment,
)

SCHEMA_VERSION = "1"
REDACTED = "[REDACTED]"
ALLOWED_FIELDS = frozenset({
    "deployment_id", "environment", "service_id", "staging_url",
    "deployed_commit", "artifact_sha256", "deployed_at",
    "health_checked_at", "health_status_code", "health_check_passed",
    "rollback_commit", "rollback_target_verified", "operator_approved",
    "production_target", "secrets_included",
})
_SENSITIVE_VALUE = re.compile(
    r"(?:bearer\\s+|sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|"
    r"github_pat_[A-Za-z0-9_]{8,}|AIza[A-Za-z0-9_-]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{8,}|(?:api[_-]?key|access[_-]?token|"
    r"password|passwd|secret|token)\\s*[:=])",
    re.IGNORECASE,
)


def _safe_metadata(key: str, value: Any) -> Any:
    """Return bounded JSON-safe metadata and redact credential-like strings."""
    if value is None or isinstance(value, (bool, int)):
        return value
    if not isinstance(value, str):
        return None
    bounded = value[:512]
    if _SENSITIVE_VALUE.search(bounded):
        return REDACTED
    if key == "staging_url":
        try:
            parsed = urlsplit(bounded)
            if (parsed.username or parsed.password or parsed.query
                    or parsed.fragment or parsed.path not in ("", "/")):
                return REDACTED
        except ValueError:
            return REDACTED
    return bounded


def _canonical_fingerprint(evidence: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        dict(evidence), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def collect_staging_evidence(
    raw_evidence: Mapping[str, Any], *, expected_commit: str
) -> dict:
    if not isinstance(raw_evidence, Mapping):
        raise TypeError("raw_evidence must be a mapping")

    # Unknown input is deliberately discarded; values are never copied to output.
    selected = {
        key: raw_evidence[key]
        for key in ALLOWED_FIELDS
        if key in raw_evidence
    }
    normalized = {
        key: _safe_metadata(key, value)
        for key, value in selected.items()
    }

    evidence = StagingDeploymentEvidence(**normalized)
    evaluation = evaluate_staging_deployment(
        evidence, expected_commit=expected_commit
    )
    safe_record = {
        key: value for key, value in normalized.items()
        if value is not None
    }

    return {
        "schemaVersion": SCHEMA_VERSION,
        "state": evaluation["state"],
        "ready": evaluation["ready"],
        "checks": evaluation["checks"],
        "evidence": safe_record,
        "evidenceFingerprintSha256": _canonical_fingerprint(safe_record),
        "unknownFieldCount": len(set(raw_evidence) - ALLOWED_FIELDS),
        "secretsIncludedInReport": False,
        "rawInputIncluded": False,
        "deploymentPerformed": False,
        "healthProbePerformed": False,
        "rollbackPerformed": False,
        "providerCallsPerformed": False,
        "liveTestAuthorized": False,
    }


def validate_collected_report(report: Mapping[str, Any]) -> bool:
    """Check schema, allowlist, redaction, fingerprint, and safety invariants."""
    if not isinstance(report, Mapping) or report.get("schemaVersion") != SCHEMA_VERSION:
        return False
    evidence = report.get("evidence")
    fingerprint = report.get("evidenceFingerprintSha256")
    if not isinstance(evidence, Mapping) or not isinstance(fingerprint, str):
        return False
    if set(evidence) - ALLOWED_FIELDS:
        return False
    # A report must already contain sanitized values; never trust a recomputed hash alone.
    for key, value in evidence.items():
        if _safe_metadata(key, value) != value:
            return False
    if fingerprint != _canonical_fingerprint(evidence):
        return False
    required_false_flags = (
        "secretsIncludedInReport", "rawInputIncluded", "deploymentPerformed",
        "healthProbePerformed", "rollbackPerformed", "providerCallsPerformed",
        "liveTestAuthorized",
    )
    return all(report.get(flag) is False for flag in required_false_flags)
