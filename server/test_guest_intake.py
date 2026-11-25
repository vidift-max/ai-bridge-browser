import unittest

from server.guest_intake import validate_guest_application
from server.messenger_backend import MessengerBackend


class GuestIntakeTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend(
            {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"},
            {})
        self.backend.create_conversation(
            "admin-token", "guest-room", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.invite = self.backend.create_room_invite(
            "admin-token", "guest-room", expires_in_seconds=600, max_uses=3)

    def tearDown(self):
        self.backend.close()

    def payload(self, name="External Guest", provider="CLAUDE"):
        return {"inviteToken": self.invite["token"],
                "displayName": name, "providerClaim": provider}

    def test_validation_normalizes_name_and_marks_provider_unverified(self):
        result = validate_guest_application({
            "inviteToken": self.invite["token"],
            "displayName": "  External\u0000   Guest ",
            "providerClaim": "claude"})
        self.assertEqual(result["displayName"], "External Guest")
        self.assertFalse(result["providerVerified"])

    def test_validation_rejects_extra_fields_and_unknown_provider(self):
        with self.assertRaisesRegex(ValueError, "invalid_guest_application"):
            validate_guest_application({**self.payload(), "bearerToken": "secret"})
        with self.assertRaisesRegex(ValueError, "invalid_guest_application"):
            validate_guest_application(self.payload(provider="CLAUDE-IMPERSONATOR"))

    def test_public_application_does_not_grant_room_access_or_identity(self):
        result = self.backend.submit_public_guest_application(self.payload())
        self.assertEqual(result["status"], "PENDING")
        self.assertFalse(result["providerVerified"])
        self.assertFalse(result["accessGranted"])
        self.assertNotIn(result["displayName"], self.backend.conversation_members()["guest-room"])
        self.assertNotIn("token", result)
        self.assertNotIn("bearerToken", result)

    def test_repeated_application_is_idempotent_with_same_status_capability(self):
        import base64
        capability = base64.urlsafe_b64encode(bytes([4]) * 32).decode("ascii").rstrip("=")
        payload = {**self.payload(), "statusCapability": capability}
        first = self.backend.submit_public_guest_application(payload)
        second = self.backend.submit_public_guest_application(payload)
        self.assertEqual(first["applicationId"], second["applicationId"])
        self.assertTrue(second["idempotentReplay"])

    def test_only_room_admin_can_review_and_approve_is_not_access(self):
        application = self.backend.submit_public_guest_application(self.payload())
        with self.assertRaisesRegex(PermissionError, "room_admin_required"):
            self.backend.list_guest_applications("member-token", "guest-room")
        with self.assertRaisesRegex(PermissionError, "room_admin_required"):
            self.backend.decide_guest_application(
                "member-token", "guest-room", application["applicationId"], "APPROVE")
        approved = self.backend.decide_guest_application(
            "admin-token", "guest-room", application["applicationId"], "APPROVE")
        self.assertEqual(approved["status"], "APPROVED_AWAITING_PROVISIONING")
        self.assertNotIn("AI-EXTERNAL", self.backend.conversation_members()["guest-room"])

    def test_rejection_is_terminal_and_invalid_decisions_fail(self):
        application = self.backend.submit_public_guest_application(self.payload())
        rejected = self.backend.decide_guest_application(
            "admin-token", "guest-room", application["applicationId"], "REJECT")
        self.assertEqual(rejected["status"], "REJECTED")
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.backend.decide_guest_application(
                "admin-token", "guest-room", application["applicationId"], "APPROVE")
        with self.assertRaisesRegex(ValueError, "invalid_guest_decision"):
            self.backend.decide_guest_application(
                "admin-token", "guest-room", "not-real", "MAYBE")


if __name__ == "__main__":
    unittest.main()
