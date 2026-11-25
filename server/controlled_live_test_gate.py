"""Fail-closed gate for the first controlled two-AI live test.

This module is deliberately side-effect free. It evaluates supplied evidence and
never enables provider calls, deploys services, creates rooms, or contacts APIs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveTestEvidence:
    deployed_commit: str = ""
    staging_url: str = ""
    room_id: str = ""
    room_private: bool = False
    participant_ids: tuple = ()
    sessions_registered: tuple = ()
    provider_assignments: tuple = ()
    operator_authorized: bool = False
    provider_calls_authorized: bool = False


REQUIRED_AI_IDS = ("AI-USER", "AI-PEER")


def evaluate_gate(evidence: LiveTestEvidence):
    checks = [
        ("deployed_commit", bool(evidence.deployed_commit), "staging commit identified"),
        ("staging_url", bool(evidence.staging_url), "approved staging endpoint identified"),
        ("private_two_ai_room", evidence.room_private and len(evidence.participant_ids) == 2
         and set(evidence.participant_ids) == set(REQUIRED_AI_IDS), "exactly the two required AIs are in a private room"),
        ("own_sessions_registered", set(evidence.sessions_registered) == set(REQUIRED_AI_IDS),
         "both AIs registered their own authenticated sessions"),
        ("provider_assignments", set(evidence.provider_assignments) == set(REQUIRED_AI_IDS),
         "both AIs have explicit provider assignments"),
        ("operator_authorization", evidence.operator_authorized, "operator explicitly authorized the test"),
        ("provider_call_authorization", evidence.provider_calls_authorized,
         "provider API calls are explicitly authorized for this test"),
    ]
    return {
        "state": "AUTHORIZED_FOR_OPERATOR_EXECUTION" if all(ok for _, ok, _ in checks) else "BLOCKED",
        "executionPerformed": False,
        "providerCallsPerformed": False,
        "checks": [
            {"id": key, "ok": ok, "detail": detail}
            for key, ok, detail in checks
        ],
    }
