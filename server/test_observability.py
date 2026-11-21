import unittest

from observability import OperationalEventLog


class OperationalEventLogTests(unittest.TestCase):
    def test_secret_metadata_is_filtered_and_values_are_bounded(self):
        log = OperationalEventLog(max_events=2)
        event = log.record(
            "MESSAGE_ACCEPTED",
            correlation_id="corr-1",
            principal="AI-A",
            metadata={
                "Authorization": "Bearer super-secret",
                "credential_token": "hidden",
                "safe": "x" * 300,
            },
        )
        self.assertNotIn("Authorization", event.metadata)
        self.assertNotIn("credential_token", event.metadata)
        self.assertEqual(len(event.metadata["safe"]), 256)

    def test_log_is_bounded(self):
        log = OperationalEventLog(max_events=2)
        log.record("STARTUP")
        log.record("READINESS_OK")
        log.record("MESSAGE_ACCEPTED")
        self.assertEqual(len(log.snapshot()), 2)
        self.assertEqual(log.snapshot()[0].event_type, "READINESS_OK")


if __name__ == "__main__":
    unittest.main()
