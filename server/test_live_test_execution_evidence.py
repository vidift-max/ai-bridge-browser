import unittest

from server.live_test_execution_evidence import (
    ExecutionEvidence,
    validate_execution_evidence,
)


class ExecutionEvidenceTest(unittest.TestCase):
    def complete(self, **changes):
        data = dict(
            deployed_commit="abc123",
            staging_id="staging-1",
            staging_url="https://staging.example",
            room_id="room-2ai",
            participant_ids=("AI-USER", "AI-PEER"),
            session_ai_ids=("AI-USER", "AI-PEER"),
            provider_assignments=("AI-USER", "AI-PEER"),
            request_ids=("req-user", "req-peer"),
            correlation_id="corr-1",
            started_at="2026-11-25T23:00:00Z",
            finished_at="2026-11-25T23:00:03Z",
            response_statuses=(200, 200),
        )
        data.update(changes)
        return ExecutionEvidence(**data)

    def test_complete_evidence_is_valid(self):
        result = validate_execution_evidence(self.complete())
        self.assertEqual(result["state"], "VALID")
        self.assertFalse(result["secretsStored"])
        self.assertFalse(result["providerCallsPerformed"])

    def test_stale_deployed_sha_blocks(self):
        result = validate_execution_evidence(
            self.complete(deployed_commit="old-sha"),
            expected_deployed_commit="current-sha",
        )
        self.assertEqual(result["state"], "BLOCKED")

    def test_expected_provider_mapping_must_match(self):
        result = validate_execution_evidence(
            self.complete(provider_assignments=("AI-USER", "AI-PEER")),
            expected_provider_assignments=("AI-PEER", "AI-USER"),
        )
        self.assertEqual(result["state"], "BLOCKED")

    def test_extra_participant_blocks(self):
        self.assertEqual(
            validate_execution_evidence(
                self.complete(participant_ids=("AI-USER", "AI-PEER", "AI-EXTRA"))
            )["state"],
            "BLOCKED",
        )

    def test_duplicate_session_identity_blocks(self):
        self.assertEqual(
            validate_execution_evidence(
                self.complete(session_ai_ids=("AI-USER", "AI-USER"))
            )["state"],
            "BLOCKED",
        )

    def test_missing_correlation_or_status_blocks(self):
        for changes in (
            {"correlation_id": ""},
            {"response_statuses": ()},
            {"started_at": ""},
        ):
            self.assertEqual(
                validate_execution_evidence(self.complete(**changes))["state"],
                "BLOCKED",
            )


if __name__ == "__main__":
    unittest.main()
