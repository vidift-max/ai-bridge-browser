import unittest
from datetime import datetime, timedelta, timezone

from server.credential_registry import CredentialRegistry
from server.session_registry import SessionRegistry


class LifecycleEdgeCaseTests(unittest.TestCase):
    def test_credential_is_expired_at_exact_boundary(self):
        now = datetime(2026, 11, 21, 22, 30, tzinfo=timezone.utc)
        registry = CredentialRegistry({"token-a": "ai-a"}, {"token-a": now})
        self.assertEqual(registry.status("token-a", now), "EXPIRED")
        with self.assertRaises(PermissionError):
            registry.authenticate("token-a", now)

    def test_credential_remains_active_one_microsecond_before_expiry(self):
        expiry = datetime(2026, 11, 21, 22, 30, tzinfo=timezone.utc)
        before = expiry - timedelta(microseconds=1)
        registry = CredentialRegistry({"token-a": "ai-a"}, {"token-a": expiry})
        self.assertEqual(registry.authenticate("token-a", before), "ai-a")

    def test_session_is_expired_at_exact_boundary(self):
        now = datetime(2026, 11, 21, 22, 30, tzinfo=timezone.utc)
        registry = SessionRegistry()
        registry.create("session-a", "ai-a", now)
        self.assertEqual(registry.status("session-a", now), "EXPIRED")
        with self.assertRaises(PermissionError):
            registry.authenticate("session-a", now)


if __name__ == "__main__":
    unittest.main()
