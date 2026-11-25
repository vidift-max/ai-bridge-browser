"""Fail-closed operator execution record for the first two-AI live turn.

This module records authorization/execution state only. It performs no network
I/O and never stores provider credentials, bearer tokens, prompts, or bodies.
"""

from dataclasses import dataclass
from typing import Optional

from server.live_test_execution_evidence import (
    ExecutionEvidence,
    REQUIRED_AI_IDS,
    validate_execution_evidence,
)

BLOCKED = "BLOCKED"
AUTHORIZED = "AUTHORIZED_FOR_OPERATOR_EXECUTION"
EXECUTED = "EXECUTED_FIRST_TURN"


@dataclass(frozen=True)
class OperatorExecutionRecord:
    state: str
    operator_authorized: bool = False
    provider_calls_authorized: bool = False
    execution_started: bool = False
    execution_finished: bool = False
    first_round_trip_succeeded: bool = False
    stopped_after_first_round_trip: bool = False
    deployed_commit: str = ""
    room_id: str = ""
    participant_ids: tuple = ()
    session_ai_ids: tuple = ()
    provider_assignments: tuple = ()
    correlation_id: str = ""
    failure_code: str = ""


def evaluate_operator_record(
    record: OperatorExecutionRecord,
    evidence: Optional[ExecutionEvidence] = None,
    *,
    expected_deployed_commit: Optional[str] = None,
    expected_provider_assignments: Optional[tuple] = None,
):
    errors = []

    if record.state not in {BLOCKED, AUTHORIZED, EXECUTED}:
        errors.append("invalid state")

    if record.state == AUTHORIZED:
        if not record.operator_authorized:
            errors.append("operator authorization is required")
        if not record.provider_calls_authorized:
            errors.append("provider-call authorization is required")
        if record.execution_started or record.execution_finished:
            errors.append("authorized state cannot claim execution")
        if record.first_round_trip_succeeded or record.stopped_after_first_round_trip:
            errors.append("authorized state cannot claim a completed turn")

    if record.state == EXECUTED:
        if evidence is None:
            errors.append("executed state requires execution evidence")
        if not (record.operator_authorized and record.provider_calls_authorized):
            errors.append("executed state requires both authorizations")
        if not (record.execution_started and record.execution_finished):
            errors.append("executed state requires start and finish markers")
        if not record.first_round_trip_succeeded:
            errors.append("executed state requires first round-trip success")
        if not record.stopped_after_first_round_trip:
            errors.append("executed state requires explicit first-turn stop")
        if record.failure_code:
            errors.append("executed state cannot contain a failure code")

    if record.state == BLOCKED and record.first_round_trip_succeeded:
        errors.append("blocked state cannot claim successful round trip")

    if evidence is not None:
        evidence_result = validate_execution_evidence(
            evidence,
            expected_deployed_commit=expected_deployed_commit,
            expected_provider_assignments=expected_provider_assignments,
        )
        if evidence_result["state"] != "VALID":
            errors.append("execution evidence is not valid")
        if record.deployed_commit and record.deployed_commit != evidence.deployed_commit:
            errors.append("deployed commit mismatch")
        if record.room_id and record.room_id != evidence.room_id:
            errors.append("room mismatch")
        if record.participant_ids and tuple(record.participant_ids) != tuple(evidence.participant_ids):
            errors.append("participant mismatch")
        if record.session_ai_ids and tuple(record.session_ai_ids) != tuple(evidence.session_ai_ids):
            errors.append("session mismatch")
        if record.provider_assignments and tuple(record.provider_assignments) != tuple(evidence.provider_assignments):
            errors.append("provider mapping mismatch")
        if record.correlation_id and record.correlation_id != evidence.correlation_id:
            errors.append("correlation mismatch")

    # The record itself is metadata-only; no provider/network execution occurs.
    result_state = record.state if not errors else BLOCKED
    return {
        "state": result_state,
        "valid": not errors,
        "errors": errors,
        "executionPerformed": False,
        "providerCallsPerformed": False,
        "secretsStored": False,
        "required_ai_ids": REQUIRED_AI_IDS,
    }
