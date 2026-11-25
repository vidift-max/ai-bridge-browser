import unittest

from server.live_test_execution_evidence import ExecutionEvidence, validate_execution_evidence


class ExecutionEvidenceTest(unittest.TestCase):
    def complete(self, **changes):
        data = dict(
            deployed_commit="abc123", staging_id="staging-1", staging_url="https://staging.example",
            room_id="room-2ai", participant_ids=("AI-USER", "AI-PEER"),
            session_ai_ids=("AI-USER", "AI-PEER"),
            provider_assignments=(("AI-USER", "openai"), ("AI-PEER", "anthropic")),
            request_ids=("req-user", "req-peer"), correlation_id="corr-1",
            started_at="2026-11-25T23:00:00Z", finished_at="2026-11-25T23:00:03Z",
            response_statuses=(200, 200), turn_direction="AI-USER->AI-PEER",
            stopped_after_first_round_trip=True,
        )
        data.update(changes)
        return ExecutionEvidence(**data)

    def test_complete_evidence_is_valid(self):
        result = validate_execution_evidence(self.complete())
        self.assertEqual(result["state"], "VALID")
        self.assertFalse(result["secretsStored"])
        self.assertFalse(result["providerCallsPerformed"])

    def test_stale_sha_blocks(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(deployed_commit="old"), expected_deployed_commit="new")["state"], "BLOCKED")

    def test_provider_mapping_must_match(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(), expected_provider_assignments=(("AI-USER", "gemini"), ("AI-PEER", "anthropic"))
        )["state"], "BLOCKED")

    def test_missing_provider_id_blocks(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(provider_assignments=(("AI-USER", ""), ("AI-PEER", "anthropic")))
        )["state"], "BLOCKED")

    def test_extra_participant_blocks(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(participant_ids=("AI-USER", "AI-PEER", "AI-EXTRA"))
        )["state"], "BLOCKED")

    def test_duplicate_session_blocks(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(session_ai_ids=("AI-USER", "AI-USER"))
        )["state"], "BLOCKED")

    def test_wrong_turn_direction_blocks(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(turn_direction="AI-PEER->AI-USER")
        )["state"], "BLOCKED")

    def test_second_turn_not_allowed(self):
        self.assertEqual(validate_execution_evidence(
            self.complete(stopped_after_first_round_trip=False)
        )["state"], "BLOCKED")

    def test_missing_correlation_status_or_start_blocks(self):
        for changes in ({"correlation_id": ""}, {"response_statuses": ()}, {"started_at": ""}):
            self.assertEqual(validate_execution_evidence(self.complete(**changes))["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
