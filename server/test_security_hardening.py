import unittest
from datetime import datetime, timedelta, timezone

from server.audit import AuditLog
from server.auth import Authenticator
from server.rate_limit import RateLimitExceeded, SlidingWindowRateLimiter
from server.session_registry import SessionRegistry


class SecurityHardeningTests(unittest.TestCase):
    def test_audit_does_not_record_secret(self):
        audit = AuditLog()
        auth = Authenticator({"secret-token": "ai-a"}, audit)
        auth.authenticate("secret-token")
        event = audit.events()[-1]
        self.assertEqual(event.ai_id, "ai-a")
        self.assertNotIn("secret-token", repr(event))

    def test_generation_binding_rejects_stale_generation(self):
        registry = SessionRegistry()
        registry.create("s1", "ai-a", credential_generation=2)
        with self.assertRaises(PermissionError):
            registry.authenticate_bound("s1", 1)
        self.assertEqual(registry.authenticate_bound("s1", 2).ai_id, "ai-a")

    def test_rate_limit_blocks_fourth_event(self):
        limiter = SlidingWindowRateLimiter(max_events=3, window_seconds=60)
        now = datetime(2026, 11, 21, 22, 30, tzinfo=timezone.utc)
        limiter.allow("ai-a", now)
        limiter.allow("ai-a", now + timedelta(seconds=1))
        limiter.allow("ai-a", now + timedelta(seconds=2))
        with self.assertRaises(RateLimitExceeded):
            limiter.allow("ai-a", now + timedelta(seconds=3))

    def test_rate_limit_allows_after_window(self):
        limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        now = datetime(2026, 11, 21, 22, 30, tzinfo=timezone.utc)
        limiter.allow("ai-a", now)
        self.assertTrue(limiter.allow("ai-a", now + timedelta(seconds=61)))


if __name__ == "__main__":
    unittest.main()
