"""Non-secret evidence contract for the first controlled two-AI live test.

This module validates operator-supplied evidence only. It never contacts staging
or providers and never stores credentials, bearer tokens, or message content.
"""
from dataclasses import dataclass
from typing import Optional


REQUIRED_AI_IDS = ("AI-USER", "AI-PEER")


@dataclass(frozen=True)
class ExecutionEvidence:
    deployed_commit: str
    staging_id: str
    staging_url: str
    room_id: str
    participant_ids: tuple
    session_ai_ids: tuple
    provider_assignments: tuple
    request_ids: tuple = ()
    correlation_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    response_statuses: tuple = ()


def _unique_exact(values, expected):
    return len(values) == len(set(values)) and set(values) == set(expected)


def validate_execution_evidence(
    evidence: ExecutionEvidence,
    *,
    expected_deployed_commit: Optional[str] = None,
    expected_provider_assignments: Optional[tuple] = None,
):
    checks = []

    checks.append((
        "deployed_commit",
        bool(evidence.deployed_commit)
        and (expected_deployed_commit is None
             or evidence.deployed_commit == expected_deployed_commit),
        "deployed commit identified and matches expected staging SHA"
        if expected_deployed_commit is not None else "deployed commit identified",
    ))
    checks.append((
        "staging_identity",
        bool(evidence.staging_id) and bool(evidence.staging_url),
        "staging identifier and endpoint identified",
    ))
    checks.append((
        "exact_participants",
        _unique_exact(evidence.participant_ids, REQUIRED_AI_IDS),
        "room contains exactly AI-USER and AI-PEER",
    ))
    checks.append((
        "exact_sessions",
        _unique_exact(evidence.session_ai_ids, REQUIRED_AI_IDS),
        "both required AIs have their own registered session",
    ))
    checks.append((
        "exact_provider_assignments",
        _unique_exact(evidence.provider_assignments, REQUIRED_AI_IDS)
        and (
            expected_provider_assignments is None
            or tuple(evidence.provider_assignments) == tuple(expected_provider_assignments)
        ),
        "provider assignment evidence is complete and matches the expected mapping"
        if expected_provider_assignments is not None
        else "provider assignment evidence is complete",
    ))
    checks.append(("correlation_id", bool(evidence.correlation_id), "correlation ID recorded"))
    checks.append(("started_at", bool(evidence.started_at), "start timestamp recorded"))
    checks.append(("response_statuses", bool(evidence.response_statuses), "response status metadata recorded"))

    ok = all(item[1] for item in checks)
    return {
        "state": "VALID" if ok else "BLOCKED",
        "checks": [
            {"id": key, "ok": value, "detail": detail}
            for key, value, detail in checks
        ],
        "secretsStored": False,
        "providerCallsPerformed": False,
    }
