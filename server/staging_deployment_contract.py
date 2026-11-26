"""Offline contract for recording and reviewing a controlled staging deployment.

This module validates operator-supplied metadata. It does not deploy, probe,
rollback, access secrets, or authorize a live provider conversation.
"""
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

BLOCKED = "BLOCKED"
READY_FOR_STAGING_HANDOFF_REVIEW = "READY_FOR_STAGING_HANDOFF_REVIEW"


@dataclass(frozen=True)
class StagingDeploymentEvidence:
    deployment_id: str = ""
    environment: str = ""
    service_id: str = ""
    staging_url: str = ""
    deployed_commit: str = ""
    artifact_sha256: str = ""
    deployed_at: str = ""
    health_checked_at: str = ""
    health_status_code: int = 0
    health_check_passed: bool = False
    rollback_commit: str = ""
    rollback_target_verified: bool = False
    operator_approved: bool = False
    production_target: bool = False
    secrets_included: bool = False


def _aware_timestamp(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _valid_https_staging_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
        )
    except (TypeError, ValueError):
        return False


def evaluate_staging_deployment(
    evidence: StagingDeploymentEvidence, *, expected_commit: str
) -> dict:
    checks = []

    def add(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "ok": bool(ok), "detail": detail})

    deployed_at = _aware_timestamp(evidence.deployed_at)
    health_at = _aware_timestamp(evidence.health_checked_at)
    status = evidence.health_status_code
    valid_status = isinstance(status, int) and not isinstance(status, bool) and 200 <= status < 300

    add("staging_only", evidence.environment == "staging" and evidence.production_target is False,
        "target must be explicitly staging, never production")
    add("deployment_identity", bool(evidence.deployment_id.strip()) and bool(evidence.service_id.strip()),
        "deployment and service identifiers are required")
    add("https_staging_url", _valid_https_staging_url(evidence.staging_url),
        "staging URL must be HTTPS without embedded credentials, query, or fragment")
    add("exact_commit", bool(expected_commit) and evidence.deployed_commit == expected_commit,
        "deployed commit must match the approved SHA exactly")
    digest = evidence.artifact_sha256
    add("artifact_digest", isinstance(digest, str) and len(digest) == 64
        and all(ch in "0123456789abcdefABCDEF" for ch in digest),
        "artifact SHA-256 must contain exactly 64 hexadecimal characters")
    add("deployment_timestamp", deployed_at is not None,
        "deployment timestamp must include a timezone")
    add("health_evidence", evidence.health_check_passed is True and valid_status
        and health_at is not None and deployed_at is not None
        and health_at >= deployed_at,
        "health check must pass with a 2xx status after deployment")
    add("rollback_plan", bool(evidence.rollback_commit.strip())
        and evidence.rollback_commit != evidence.deployed_commit
        and evidence.rollback_target_verified is True,
        "a distinct, verified rollback target is required")
    add("operator_approval", evidence.operator_approved is True,
        "operator approval must be explicitly recorded")
    add("secret_hygiene", evidence.secrets_included is False,
        "deployment evidence must not contain secret material")

    ready = all(check["ok"] for check in checks)
    return {
        "state": READY_FOR_STAGING_HANDOFF_REVIEW if ready else BLOCKED,
        "ready": ready,
        "checks": checks,
        "deploymentPerformed": False,
        "healthProbePerformed": False,
        "rollbackPerformed": False,
        "providerCallsPerformed": False,
        "secretsRead": False,
        "secretsStored": False,
        "liveTestAuthorized": False,
    }
