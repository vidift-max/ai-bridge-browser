"""Offline adapter for operator-supplied staging verification records.

This validates structure, declared identity, and a canonical record digest. It
cannot authenticate the source or prove that a health probe actually occurred.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

SCHEMA_VERSION = "1"
FIELDS = frozenset({
    "environment", "service_id", "staging_url", "verified_commit",
    "artifact_sha256", "checked_at", "health_status_code",
    "health_check_passed", "verifier_identity", "source_kind",
    "probe_execution_claimed",
})
SOURCE_KINDS = frozenset({"operator_supplied", "automated_probe_record"})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def canonical_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash a canonical JSON record; this is integrity, not source authentication."""
    payload = {key: record[key] for key in FIELDS if key in record}
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp_is_aware(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _valid_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def adapt_staging_verification(
    raw_record: Mapping[str, Any],
    *,
    expected_commit: str,
    expected_service_id: str,
    expected_staging_url: str,
) -> dict:
    if not isinstance(raw_record, Mapping):
        raise TypeError("raw_record must be a mapping")

    record = {key: raw_record[key] for key in FIELDS if key in raw_record}
    supplied_digest = raw_record.get("source_record_sha256")
    calculated_digest = canonical_record_sha256(record)

    checks = {
        "environmentIsStaging": record.get("environment") == "staging",
        "serviceIdentityMatches": (
            isinstance(record.get("service_id"), str)
            and record.get("service_id") == expected_service_id
        ),
        "stagingUrlMatches": (
            _valid_https_url(record.get("staging_url"))
            and record.get("staging_url") == expected_staging_url
            and _valid_https_url(expected_staging_url)
        ),
        "commitMatches": (
            isinstance(record.get("verified_commit"), str)
            and record.get("verified_commit") == expected_commit
            and bool(HEX40.fullmatch(expected_commit) or HEX64.fullmatch(expected_commit))
        ),
        "artifactDigestValid": (
            isinstance(record.get("artifact_sha256"), str)
            and bool(HEX64.fullmatch(record.get("artifact_sha256", "")))
        ),
        "timestampIsTimezoneAware": _timestamp_is_aware(record.get("checked_at")),
        "healthStatusIs2xxInteger": (
            isinstance(record.get("health_status_code"), int)
            and not isinstance(record.get("health_status_code"), bool)
            and 200 <= record.get("health_status_code", 0) < 300
        ),
        "healthCheckPassed": record.get("health_check_passed") is True,
        "verifierIdentityPresent": (
            isinstance(record.get("verifier_identity"), str)
            and 1 <= len(record.get("verifier_identity", "")) <= 128
            and not re.search(r"(?:bearer\\s+|token\\s*[:=]|password\\s*[:=])",
                              record.get("verifier_identity", ""), re.IGNORECASE)
        ),
        "sourceKindAllowed": record.get("source_kind") in SOURCE_KINDS,
        "sourceRecordDigestMatches": (
            isinstance(supplied_digest, str)
            and bool(HEX64.fullmatch(supplied_digest))
            and supplied_digest == calculated_digest
        ),
    }
    if record.get("source_kind") == "automated_probe_record":
        checks["automatedProbeClaimPresent"] = record.get("probe_execution_claimed") is True
    elif record.get("source_kind") == "operator_supplied":
        checks["operatorRecordDoesNotClaimAdapterProbe"] = (
            record.get("probe_execution_claimed") is False
        )

    matched = all(checks.values())
    return {
        "schemaVersion": SCHEMA_VERSION,
        "state": "MATCHED_UNATTESTED" if matched else "BLOCKED",
        "matched": matched,
        "checks": checks,
        "record": record,
        "sourceRecordSha256": calculated_digest,
        "unknownFieldCount": len(set(raw_record) - FIELDS - {"source_record_sha256"}),
        "sourceIntegrityChecked": True,
        "sourceAuthenticityVerified": False,
        "probePerformedByAdapter": False,
        "deploymentPerformed": False,
        "secretsAccessed": False,
        "providerCallsPerformed": False,
        "liveTestAuthorized": False,
    }


def validate_staging_verification_report(report: Mapping[str, Any]) -> bool:
    if not isinstance(report, Mapping) or report.get("schemaVersion") != SCHEMA_VERSION:
        return False
    record = report.get("record")
    if not isinstance(record, Mapping) or set(record) - FIELDS:
        return False
    digest = report.get("sourceRecordSha256")
    if not isinstance(digest, str) or digest != canonical_record_sha256(record):
        return False
    required_false = (
        "sourceAuthenticityVerified", "probePerformedByAdapter",
        "deploymentPerformed", "secretsAccessed", "providerCallsPerformed",
        "liveTestAuthorized",
    )
    if not all(report.get(flag) is False for flag in required_false):
        return False
    checks = report.get("checks")
    if not isinstance(checks, Mapping) or not all(
        isinstance(value, bool) for value in checks.values()
    ):
        return False
    matched = all(checks.values())
    return report.get("matched") is matched and report.get("state") == (
        "MATCHED_UNATTESTED" if matched else "BLOCKED"
    )
