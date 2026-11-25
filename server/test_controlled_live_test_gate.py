import unittest

from server.controlled_live_test_gate import LiveTestEvidence, evaluate_gate


class ControlledLiveTestGateTest(unittest.TestCase):
    def complete(self, **changes):
        data = dict(
            deployed_commit="abc123",
            staging_url="https://staging.invalid",
            room_id="room-2ai",
            room_private=True,
            participant_ids=("AI-USER", "AI-PEER"),
            sessions_registered=("AI-USER", "AI-PEER"),
            provider_assignments=("AI-USER", "AI-PEER"),
            operator_authorized=True,
            provider_calls_authorized=True,
        )
        data.update(changes)
        return LiveTestEvidence(**data)

    def test_complete_evidence_authorizes_execution_but_performs_nothing(self):
        result = evaluate_gate(self.complete())
        self.assertEqual(result["state"], "AUTHORIZED_FOR_OPERATOR_EXECUTION")
        self.assertFalse(result["executionPerformed"])
        self.assertFalse(result["providerCallsPerformed"])

    def test_missing_operator_authorization_blocks(self):
        self.assertEqual(
            evaluate_gate(self.complete(operator_authorized=False))["state"], "BLOCKED")

    def test_provider_call_authorization_is_independent(self):
        result = evaluate_gate(self.complete(provider_calls_authorized=False))
        self.assertEqual(result["state"], "BLOCKED")
        check = next(x for x in result["checks"] if x["id"] == "provider_call_authorization")
        self.assertFalse(check["ok"])

    def test_room_must_be_private_and_exactly_two_required_ids(self):
        for evidence in (
            self.complete(room_private=False),
            self.complete(participant_ids=("AI-USER",)),
            self.complete(participant_ids=("AI-USER", "AI-PEER", "AI-EXTRA")),
            self.complete(participant_ids=("AI-USER", "AI-OTHER")),
        ):
            self.assertEqual(evaluate_gate(evidence)["state"], "BLOCKED")

    def test_each_ai_must_have_own_registered_session(self):
        result = evaluate_gate(self.complete(sessions_registered=("AI-USER",)))
        self.assertEqual(result["state"], "BLOCKED")

    def test_each_ai_must_have_provider_assignment(self):
        result = evaluate_gate(self.complete(provider_assignments=("AI-USER",)))
        self.assertEqual(result["state"], "BLOCKED")

    def test_missing_staging_identity_blocks(self):
        self.assertEqual(evaluate_gate(self.complete(deployed_commit=""))["state"], "BLOCKED")
        self.assertEqual(evaluate_gate(self.complete(staging_url=""))["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
