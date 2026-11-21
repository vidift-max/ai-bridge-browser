import unittest
from datetime import datetime, timedelta, timezone

from server.session_registry import SessionRegistry


class SessionRegistryTest(unittest.TestCase):
    def test_active_and_expired(self):
        registry = SessionRegistry()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        registry.create("S1", "AI-A", now + timedelta(minutes=5))
        self.assertEqual(registry.authenticate("S1", now).ai_id, "AI-A")
        with self.assertRaises(PermissionError):
            registry.authenticate("S1", now + timedelta(minutes=5))
        self.assertEqual(registry.status("S1"), "EXPIRED")

    def test_revoke_blocks_session(self):
        registry = SessionRegistry()
        registry.create("S1", "AI-A")
        registry.revoke("S1")
        self.assertEqual(registry.status("S1"), "REVOKED")
        with self.assertRaises(PermissionError):
            registry.authenticate("S1")

    def test_unknown_session_rejected(self):
        with self.assertRaises(PermissionError):
            SessionRegistry().authenticate("UNKNOWN")


if __name__ == "__main__":
    unittest.main()
