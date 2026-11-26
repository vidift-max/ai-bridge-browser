import unittest

from server.live_test_readiness_audit import (
    BLOCKED,
    READY_FOR_OPERATOR_REVIEW,
    LiveTestReadinessSnapshot,
    evaluate_live_test_readiness,
)


EXPECTED = (("AI-USER", "openai"), ("AI-PEER", "anthropic"))


class LiveTestReadinessAuditTest(unittest.TestCase):
    def snapshot(self, **changes):
        data = dict(
            deployed_commit="approved-sha",
            staging_id="staging-186",
            staging_url="https://staging.example",
            staging_health_verified=True,
            room_id="private-room-186",
            room_private=True,
            participant_ids=("AI-USER", "AI-PEER"),
            session_ai_ids=("AI-USER", "AI-PEER"),
            provider_assignments=EXPECTED,
            provider_readiness_verified=True,
            operator_authorization_recorded=True,
            provider_calls_authorization_recorded=True,
            stop_conditions_reviewed=True,
        )
        data.update(changes)
        return LiveTestReadinessSnapshot(**data)

    def test_complete_snapshot_only_ready_for_operator_review(self):
        result = evaluate_live_test_readiness(
            self.snapshot(), expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)
        self.assertEqual(result["state"], READY_FOR_OPERATOR_REVIEW)
        self.assertTrue(result["ready"])
        self.assertFalse(result["executionAuthorized"])
        self.assertFalse(result["executionPerformed"])
        self.assertFalse(result["providerCallsPerformed"])
        self.assertFalse(result["networkCallsPerformed"])
        self.assertFalse(result["secretsStored"])

    def test_default_snapshot_blocked(self):
        result = evaluate_live_test_readiness(
            LiveTestReadinessSnapshot(),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)
        self.assertEqual(result["state"], BLOCKED)

    def test_wrong_deployed_sha_blocks(self):
        self.assertEqual(evaluate_live_test_readiness(
            self.snapshot(deployed_commit="stale"),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_missing_staging_identity_blocks(self):
        self.assertEqual(evaluate_live_test_readiness(
            self.snapshot(staging_url=""),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_unhealthy_staging_blocks(self):
        self.assertEqual(evaluate_live_test_readiness(
            self.snapshot(staging_health_verified=False),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_public_or_unidentified_room_blocks(self):
        for changes in ({"room_private": False}, {"room_id": ""}):
            self.assertEqual(evaluate_live_test_readiness(
                self.snapshot(**changes), expected_deployed_commit="approved-sha",
                expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_extra_or_reordered_participant_blocks(self):
        for participants in (("AI-USER", "AI-PEER", "AI-EXTRA"),
                             ("AI-PEER", "AI-USER")):
            self.assertEqual(evaluate_live_test_readiness(
                self.snapshot(participant_ids=participants),
                expected_deployed_commit="approved-sha",
                expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_missing_peer_session_blocks(self):
        self.assertEqual(evaluate_live_test_readiness(
            self.snapshot(session_ai_ids=("AI-USER",)),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_provider_mapping_mismatch_blocks(self):
        self.assertEqual(evaluate_live_test_readiness(
            self.snapshot(provider_assignments=(("AI-USER", "openai"),
                                                ("AI-PEER", "gemini"))),
            expected_deployed_commit="approved-sha",
            expected_provider_assignments=EXPECTED)["state"], BLOCKED)

    def test_provider_readiness_and_authorizations_are_separate(self):
        for changes in (
            {"provider_readiness_verified": False},
            {"operator_authorization_recorded": False},
            {"provider_calls_authorization_recorded": False},
            {"stop_conditions_reviewed": False},
        ):
            self.assertEqual(evaluate_live_test_readiness(
                self.snapshot(**changes), expected_deployed_commit="approved-sha",
                expected_provider_assignments=EXPECTED)["state"], BLOCKED)


if __name__ == "__main__":
    unittest.main()
