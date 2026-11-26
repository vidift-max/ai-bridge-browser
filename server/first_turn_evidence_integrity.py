"""Integrity checks for first-turn evidence metadata; no network or provider I/O."""

from datetime import datetime

from server.live_test_execution_evidence import (
    ExecutionEvidence,
    validate_execution_evidence,
)


def _valid_timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def validate_first_turn_integrity(
    evidence: ExecutionEvidence,
    *,
    expected_deployed_commit=None,
    expected_provider_assignments=None,
):
    base = validate_execution_evidence(
        evidence,
        expected_deployed_commit=expected_deployed_commit,
        expected_provider_assignments=expected_provider_assignments,
    )

    request_ids = evidence.request_ids
    requests_ok = (
        isinstance(request_ids, (tuple, list))
        and len(request_ids) == 2
        and all(isinstance(item, str) and item.strip() for item in request_ids)
        and len(set(request_ids)) == 2
    )

    statuses = evidence.response_statuses
    statuses_ok = (
        isinstance(statuses, (tuple, list))
        and len(statuses) == 2
        and all(type(status) is int and 200 <= status < 300 for status in statuses)
    )

    started = _valid_timestamp(evidence.started_at)
    finished = _valid_timestamp(evidence.finished_at)
    time_ok = started is not None and finished is not None and started <= finished

    checks = [
        {"id": "exact_request_ids", "ok": requests_ok,
         "detail": "two distinct non-empty request IDs recorded"},
        {"id": "successful_response_statuses", "ok": statuses_ok,
         "detail": "exactly two integer 2xx response statuses recorded"},
        {"id": "ordered_aware_timestamps", "ok": time_ok,
         "detail": "timezone-aware start and finish timestamps are valid and ordered"},
    ]
    checks.extend(base["checks"])
    valid = base["state"] == "VALID" and all(item["ok"] for item in checks)

    return {
        "state": "VALID" if valid else "BLOCKED",
        "checks": checks,
        "secretsStored": False,
        "providerCallsPerformed": False,
        "networkCallsPerformed": False,
    }
