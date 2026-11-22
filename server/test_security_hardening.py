import unittest
from concurrent.futures import ThreadPoolExecutor
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


    def test_rate_limit_isolated_per_ai_principal(self):
        limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        self.assertTrue(limiter.allow("ai-a"))
        self.assertTrue(limiter.allow("ai-b"))
        with self.assertRaises(RateLimitExceeded):
            limiter.allow("ai-a")

    def test_rate_limit_is_atomic_under_concurrent_requests(self):
        limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        def attempt(_):
            try:
                limiter.allow("ai-a")
                return "allowed"
            except RateLimitExceeded:
                return "limited"
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(attempt, range(12)))
        self.assertEqual(results.count("allowed"), 1)
        self.assertEqual(results.count("limited"), 11)

if __name__ == "__main__":
    unittest.main()
