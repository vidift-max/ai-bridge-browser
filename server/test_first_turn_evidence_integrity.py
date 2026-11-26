import unittest

from server.live_test_execution_evidence import ExecutionEvidence
from server.first_turn_evidence_integrity import validate_first_turn_integrity


class FirstTurnEvidenceIntegrityTest(unittest.TestCase):
    def evidence(self, **changes):
        data = dict(
            deployed_commit="deploy-185",
            staging_id="staging-185",
            staging_url="https://staging.example",
            room_id="room-185",
            participant_ids=("AI-USER", "AI-PEER"),
            session_ai_ids=("AI-USER", "AI-PEER"),
            provider_assignments=(("AI-USER", "openai"), ("AI-PEER", "anthropic")),
            request_ids=("req-user", "req-peer"),
            correlation_id="corr-185",
            started_at="2026-11-25T22:00:00Z",
            finished_at="2026-11-25T22:00:03Z",
            response_statuses=(200, 201),
            turn_direction="AI-USER->AI-PEER",
            stopped_after_first_round_trip=True,
        )
        data.update(changes)
        return ExecutionEvidence(**data)

    def test_complete_evidence_valid(self):
        result = validate_first_turn_integrity(self.evidence())
        self.assertEqual(result["state"], "VALID")
        self.assertFalse(result["secretsStored"])
        self.assertFalse(result["providerCallsPerformed"])
        self.assertFalse(result["networkCallsPerformed"])

    def test_duplicate_request_id_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(request_ids=("same", "same")))["state"], "BLOCKED")

    def test_missing_request_id_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(request_ids=("req-user", "")))["state"], "BLOCKED")

    def test_wrong_status_count_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(response_statuses=(200,)))["state"], "BLOCKED")

    def test_non_2xx_status_blocks(self):
        for statuses in ((200, 500), (200, 0), (200, True), ("200", 201)):
            self.assertEqual(validate_first_turn_integrity(
                self.evidence(response_statuses=statuses))["state"], "BLOCKED")

    def test_missing_finished_timestamp_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(finished_at=""))["state"], "BLOCKED")

    def test_naive_timestamp_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(started_at="2026-11-25T22:00:00"))["state"], "BLOCKED")

    def test_finish_before_start_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(finished_at="2026-11-25T21:59:59Z"))["state"], "BLOCKED")

    def test_expected_deployment_mismatch_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(), expected_deployed_commit="different")["state"], "BLOCKED")

    def test_provider_assignment_mismatch_blocks(self):
        self.assertEqual(validate_first_turn_integrity(
            self.evidence(),
            expected_provider_assignments=(("AI-USER", "gemini"), ("AI-PEER", "anthropic"))
        )["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
