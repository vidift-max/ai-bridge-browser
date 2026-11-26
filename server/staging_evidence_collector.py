"""Offline, allowlist-based collector for staging deployment evidence.

Only approved metadata fields are copied into the report. Unknown fields (which
may include secrets) are never echoed. This module performs no I/O or probing.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from server.staging_deployment_contract import (
    BLOCKED,
    StagingDeploymentEvidence,
    evaluate_staging_deployment,
)

SCHEMA_VERSION = "1"
ALLOWED_FIELDS = frozenset({
    "deployment_id", "environment", "service_id", "staging_url",
    "deployed_commit", "artifact_sha256", "deployed_at",
    "health_checked_at", "health_status_code", "health_check_passed",
    "rollback_commit", "rollback_target_verified", "operator_approved",
    "production_target", "secrets_included",
})


def _safe_metadata(value: Any) -> Any:
    """Return only JSON-safe, bounded metadata; never stringify arbitrary objects."""
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str):
            return value[:512]
        return value
    return None


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
        key: _safe_metadata(value)
        for key, value in selected.items()
    }

    # Construct the typed record using only allowlisted keys. Malformed field
    # types remain fail-closed in the contract validator and are not echoed.
    evidence = StagingDeploymentEvidence(**normalized)
    evaluation = evaluate_staging_deployment(
        evidence, expected_commit=expected_commit
    )

    safe_record = {
        key: value for key, value in normalized.items()
        if key in ALLOWED_FIELDS and value is not None
    }
    canonical = json.dumps(
        safe_record, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    fingerprint = hashlib.sha256(canonical).hexdigest()

    return {
        "schemaVersion": SCHEMA_VERSION,
        "state": evaluation["state"],
        "ready": evaluation["ready"],
        "checks": evaluation["checks"],
        "evidence": safe_record,
        "evidenceFingerprintSha256": fingerprint,
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
    """Check report shape and ensure the fingerprint matches its safe evidence."""
    if not isinstance(report, Mapping):
        return False
    if report.get("schemaVersion") != SCHEMA_VERSION:
        return False
    evidence = report.get("evidence")
    fingerprint = report.get("evidenceFingerprintSha256")
    if not isinstance(evidence, Mapping) or not isinstance(fingerprint, str):
        return False
    if set(evidence) - ALLOWED_FIELDS:
        return False
    canonical = json.dumps(
        dict(evidence), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    expected = hashlib.sha256(canonical).hexdigest()
    return (
        fingerprint == expected
        and report.get("secretsIncludedInReport") is False
        and report.get("rawInputIncluded") is False
        and report.get("liveTestAuthorized") is False
    )
