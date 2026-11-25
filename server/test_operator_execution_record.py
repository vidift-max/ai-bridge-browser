import unittest

from server.live_test_execution_evidence import ExecutionEvidence
from server.operator_execution_record import (
    AUTHORIZED,
    BLOCKED,
    EXECUTED,
    OperatorExecutionRecord,
    evaluate_operator_record,
)


class OperatorExecutionRecordTest(unittest.TestCase):
    def evidence(self):
        return ExecutionEvidence(
            deployed_commit="deploy-184",
            staging_id="staging-184",
            staging_url="https://staging.example",
            room_id="room-184",
            participant_ids=("AI-USER", "AI-PEER"),
            session_ai_ids=("AI-USER", "AI-PEER"),
            provider_assignments=(("AI-USER", "openai"), ("AI-PEER", "anthropic")),
            request_ids=("req-1", "req-2"),
            correlation_id="corr-184",
            started_at="2026-11-25T22:00:00Z",
            finished_at="2026-11-25T22:00:03Z",
            response_statuses=(200, 200),
            turn_direction="AI-USER->AI-PEER",
            stopped_after_first_round_trip=True,
        )

    def test_authorized_is_not_executed(self):
        record = OperatorExecutionRecord(
            state=AUTHORIZED,
            operator_authorized=True,
            provider_calls_authorized=True,
        )
        result = evaluate_operator_record(record)
        self.assertEqual(result["state"], AUTHORIZED)
        self.assertTrue(result["valid"])
        self.assertFalse(result["executionPerformed"])
        self.assertFalse(result["providerCallsPerformed"])

    def test_authorized_without_provider_permission_blocks(self):
        result = evaluate_operator_record(OperatorExecutionRecord(
            state=AUTHORIZED, operator_authorized=True,
        ))
        self.assertEqual(result["state"], BLOCKED)
        self.assertFalse(result["valid"])

    def test_executed_requires_both_authorizations_and_markers(self):
        record = OperatorExecutionRecord(
            state=EXECUTED,
            operator_authorized=True,
            provider_calls_authorized=True,
            execution_started=True,
            execution_finished=True,
            first_round_trip_succeeded=True,
            stopped_after_first_round_trip=True,
        )
        result = evaluate_operator_record(record, self.evidence(),
                                           expected_deployed_commit="deploy-184",
                                           expected_provider_assignments=(
                                               ("AI-USER", "openai"), ("AI-PEER", "anthropic")))
        self.assertEqual(result["state"], EXECUTED)
        self.assertTrue(result["valid"])

    def test_executed_without_stop_blocks(self):
        result = evaluate_operator_record(OperatorExecutionRecord(
            state=EXECUTED, operator_authorized=True, provider_calls_authorized=True,
            execution_started=True, execution_finished=True, first_round_trip_succeeded=True,
        ), self.evidence())
        self.assertEqual(result["state"], BLOCKED)

    def test_blocked_cannot_claim_success(self):
        result = evaluate_operator_record(OperatorExecutionRecord(
            state=BLOCKED, first_round_trip_succeeded=True,
        ))
        self.assertEqual(result["state"], BLOCKED)
        self.assertFalse(result["valid"])

    def test_identity_mismatch_blocks(self):
        record = OperatorExecutionRecord(
            state=EXECUTED, operator_authorized=True, provider_calls_authorized=True,
            execution_started=True, execution_finished=True, first_round_trip_succeeded=True,
            stopped_after_first_round_trip=True, room_id="wrong",
        )
        result = evaluate_operator_record(record, self.evidence())
        self.assertEqual(result["state"], BLOCKED)

    def test_unknown_state_blocks(self):
        result = evaluate_operator_record(OperatorExecutionRecord(state="READY"))
        self.assertEqual(result["state"], BLOCKED)


if __name__ == "__main__":
    unittest.main()
