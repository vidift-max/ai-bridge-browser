import unittest
from datetime import timedelta

from server.guest_web_session import GuestWebSessionService


class FakeAuthenticator:
    def __init__(self):
        self.tokens = {"guest-bearer": ("AI-GUEST-0001", "ACTIVE")}
        self.ephemeral = {}

    def authenticate(self, token):
        record = self.tokens.get(token) or self.ephemeral.get(token)
        if not record or record[1] != "ACTIVE":
            raise PermissionError("authentication_required")
        return type("Principal", (), {"ai_id": record[0]})()

    def provision_ephemeral_credential(self, token, ai_id, expires_at):
        self.ephemeral[token] = (ai_id, "ACTIVE", expires_at)

    def revoke(self, token):
        if token in self.ephemeral:
            self.ephemeral[token] = (self.ephemeral[token][0], "REVOKED")
        elif token in self.tokens:
            self.tokens[token] = (self.tokens[token][0], "REVOKED")


class GuestWebSessionServiceTest(unittest.TestCase):
    def setUp(self):
        self.auth = FakeAuthenticator()
        self.service = GuestWebSessionService(self.auth)

    def test_exchange_returns_opaque_short_lived_session(self):
        result = self.service.exchange("guest-bearer")
        self.assertTrue(result["sessionToken"])
        self.assertNotEqual(result["sessionToken"], "guest-bearer")
        self.assertEqual(result["aiId"], "AI-GUEST-0001")
        self.assertLessEqual(result["expiresInSeconds"], 12 * 60 * 60)
        self.assertEqual(self.service.authenticate(result["sessionToken"])["aiId"], "AI-GUEST-0001")

    def test_non_guest_credential_is_rejected(self):
        self.auth.tokens["member-token"] = ("AI-MEMBER", "ACTIVE")
        with self.assertRaisesRegex(PermissionError, "guest_credential_required"):
            self.service.exchange("member-token")

    def test_unknown_session_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.service.authenticate("unknown-session")

    def test_logout_revokes_session(self):
        session = self.service.exchange("guest-bearer")["sessionToken"]
        self.assertTrue(self.service.revoke(session))
        with self.assertRaises(PermissionError):
            self.service.authenticate(session)

    def test_parent_credential_revocation_invalidates_child_session(self):
        session = self.service.exchange("guest-bearer")["sessionToken"]
        self.auth.revoke("guest-bearer")
        with self.assertRaises(PermissionError):
            self.service.authenticate(session)

    def test_ttl_cannot_exceed_twelve_hours(self):
        with self.assertRaisesRegex(ValueError, "guest_session_ttl_invalid"):
            GuestWebSessionService(self.auth, timedelta(hours=13))


if __name__ == "__main__":
    unittest.main()
