"""Offline readiness audit for a future controlled first-turn test.

This module evaluates operator-supplied attestations only. It never deploys,
contacts providers, creates rooms, registers sessions, or authorizes execution.
"""

from dataclasses import dataclass
from typing import Tuple

BLOCKED = "BLOCKED"
READY_FOR_OPERATOR_REVIEW = "READY_FOR_OPERATOR_REVIEW"
REQUIRED_AI_IDS = ("AI-USER", "AI-PEER")


@dataclass(frozen=True)
class LiveTestReadinessSnapshot:
    deployed_commit: str = ""
    staging_id: str = ""
    staging_url: str = ""
    staging_health_verified: bool = False
    room_id: str = ""
    room_private: bool = False
    participant_ids: Tuple[str, ...] = ()
    session_ai_ids: Tuple[str, ...] = ()
    provider_assignments: Tuple[Tuple[str, str], ...] = ()
    provider_readiness_verified: bool = False
    operator_authorization_recorded: bool = False
    provider_calls_authorization_recorded: bool = False
    stop_conditions_reviewed: bool = False


def evaluate_live_test_readiness(
    snapshot: LiveTestReadinessSnapshot,
    *,
    expected_deployed_commit: str,
    expected_provider_assignments: Tuple[Tuple[str, str], ...],
):
    checks = []

    def add(check_id, ok, detail):
        checks.append({"id": check_id, "ok": bool(ok), "detail": detail})

    add("deployed_commit", bool(expected_deployed_commit) and
        snapshot.deployed_commit == expected_deployed_commit,
        "deployed SHA must match the approved SHA exactly")
    add("staging_identity", bool(snapshot.staging_id.strip()) and
        bool(snapshot.staging_url.strip()),
        "staging ID and URL must both be recorded")
    add("staging_health", snapshot.staging_health_verified is True,
        "staging health must be independently verified")
    add("private_room", bool(snapshot.room_id.strip()) and
        snapshot.room_private is True,
        "a named private room must be verified")
    add("exact_participants",
        tuple(snapshot.participant_ids) == REQUIRED_AI_IDS,
        "room must contain exactly AI-USER and AI-PEER in canonical order")
    add("own_sessions",
        tuple(snapshot.session_ai_ids) == REQUIRED_AI_IDS,
        "each AI must have its own registered session")
    add("provider_mapping",
        tuple(snapshot.provider_assignments) == tuple(expected_provider_assignments)
        and len(snapshot.provider_assignments) == 2
        and {item[0] for item in snapshot.provider_assignments} == set(REQUIRED_AI_IDS),
        "both AI IDs must map to the exact approved provider IDs")
    add("provider_readiness", snapshot.provider_readiness_verified is True,
        "provider readiness must be checked without exposing credentials")
    add("operator_authorization_recorded",
        snapshot.operator_authorization_recorded is True,
        "operator authorization record must be present")
    add("provider_call_authorization_recorded",
        snapshot.provider_calls_authorization_recorded is True,
        "provider-call authorization record must be present separately")
    add("stop_conditions_reviewed", snapshot.stop_conditions_reviewed is True,
        "failure and immediate-stop conditions must be acknowledged")

    ready = all(item["ok"] for item in checks)
    return {
        "state": READY_FOR_OPERATOR_REVIEW if ready else BLOCKED,
        "ready": ready,
        "checks": checks,
        "executionAuthorized": False,
        "executionPerformed": False,
        "providerCallsPerformed": False,
        "networkCallsPerformed": False,
        "secretsStored": False,
    }
