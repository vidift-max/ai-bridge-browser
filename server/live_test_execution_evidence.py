"""Fail-closed, non-secret evidence contract for the first two-AI turn."""

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
    turn_direction: str = ""
    stopped_after_first_round_trip: bool = False


def _unique_exact(values, expected):
    return len(values) == len(set(values)) and set(values) == set(expected)


def _valid_provider_assignments(assignments, expected=None):
    if not assignments or len(assignments) != 2 or len(set(assignments)) != 2:
        return False
    normalized = []
    for item in assignments:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            return False
        ai_id, provider_id = item
        if not ai_id or not provider_id:
            return False
        normalized.append((ai_id, provider_id))
    if set(ai for ai, _ in normalized) != set(REQUIRED_AI_IDS):
        return False
    if expected is not None:
        return tuple(normalized) == tuple(expected)
    return True


def validate_execution_evidence(
    evidence: ExecutionEvidence,
    *,
    expected_deployed_commit: Optional[str] = None,
    expected_provider_assignments: Optional[tuple] = None,
):
    checks = [
        (
            "deployed_commit",
            bool(evidence.deployed_commit)
            and (expected_deployed_commit is None or evidence.deployed_commit == expected_deployed_commit),
            "deployed commit identified and matches expected staging SHA"
            if expected_deployed_commit is not None else "deployed commit identified",
        ),
        ("staging_identity", bool(evidence.staging_id) and bool(evidence.staging_url),
         "staging identifier and endpoint identified"),
        ("room_id", bool(evidence.room_id), "room identity recorded"),
        ("exact_participants", _unique_exact(evidence.participant_ids, REQUIRED_AI_IDS),
         "room contains exactly AI-USER and AI-PEER"),
        ("exact_sessions", _unique_exact(evidence.session_ai_ids, REQUIRED_AI_IDS),
         "both required AIs have their own registered session"),
        ("provider_assignments", _valid_provider_assignments(
            evidence.provider_assignments, expected_provider_assignments),
         "each required AI is bound to a non-empty provider ID"),
        ("correlation_id", bool(evidence.correlation_id), "correlation ID recorded"),
        ("started_at", bool(evidence.started_at), "start timestamp recorded"),
        ("response_statuses", bool(evidence.response_statuses),
         "response status metadata recorded"),
        ("turn_direction", evidence.turn_direction == "AI-USER->AI-PEER",
         "first turn direction is AI-USER to AI-PEER"),
        ("first_round_trip_stop", evidence.stopped_after_first_round_trip is True,
         "operator stopped after the first successful round trip"),
    ]
    ok = all(item[1] for item in checks)
    return {
        "state": "VALID" if ok else "BLOCKED",
        "checks": [{"id": key, "ok": value, "detail": detail} for key, value, detail in checks],
        "secretsStored": False,
        "providerCallsPerformed": False,
    }
