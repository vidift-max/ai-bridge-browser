import unittest

from server.retention_policy import (
    ONE_HOUR_SECONDS, ONE_DAY_SECONDS, MESSAGE_MISSION,
    retention_seconds, expires_at, is_expired,
)

class RetentionPolicyTest(unittest.TestCase):
    def test_group_normal_is_one_hour(self):
        self.assertEqual(retention_seconds("NORMAL", "GROUP"), ONE_HOUR_SECONDS)

    def test_mission_is_one_day(self):
        self.assertEqual(retention_seconds(MESSAGE_MISSION, "GROUP"), ONE_DAY_SECONDS)

    def test_private_is_one_day(self):
        self.assertEqual(retention_seconds("NORMAL", "PRIVATE"), ONE_DAY_SECONDS)

    def test_boundary_is_expired(self):
        self.assertFalse(is_expired(100.0, "NORMAL", "GROUP", 100.0 + ONE_HOUR_SECONDS - 0.001))
        self.assertTrue(is_expired(100.0, "NORMAL", "GROUP", 100.0 + ONE_HOUR_SECONDS))

    def test_expiry_timestamp_is_deterministic(self):
        self.assertEqual(expires_at(500.0, "MISSION", "GROUP"), 500.0 + ONE_DAY_SECONDS)

if __name__ == "__main__":
    unittest.main()
