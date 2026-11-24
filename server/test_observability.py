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

    def test_summary_counts_events_without_exposing_event_identity(self):
        log = OperationalEventLog(max_events=2)
        log.record("MESSAGE_ACCEPTED", correlation_id="private-correlation", principal="AI-SECRET")
        log.record("STORAGE_FAILURE", outcome="error", diagnostic_code="STORAGE_UNAVAILABLE")
        log.record("MESSAGE_ACCEPTED")
        summary = log.summary()
        self.assertEqual(summary["eventsObserved"], 3)
        self.assertEqual(summary["eventsRetained"], 2)
        self.assertEqual(summary["eventsDropped"], 1)
        self.assertEqual(summary["outcomes"], {"error": 1, "ok": 2})
        self.assertNotIn("private-correlation", repr(summary))
        self.assertNotIn("AI-SECRET", repr(summary))
        self.assertNotIn("diagnostic_code", summary)

    def test_event_type_cardinality_is_bounded(self):
        log = OperationalEventLog(max_events=100)
        for index in range(100):
            log.record("CUSTOM_EVENT_" + str(index))
        summary = log.summary()
        self.assertLessEqual(len(summary["eventTypes"]), 32)
        self.assertEqual(summary["eventTypes"]["OTHER"], 69)

    def test_unknown_outcome_is_normalized(self):
        log = OperationalEventLog()
        event = log.record("STARTUP", outcome="Bearer super-secret")
        self.assertEqual(event.outcome, "other")
        self.assertEqual(log.summary()["outcomes"], {"other": 1})

    def test_log_is_bounded(self):
        log = OperationalEventLog(max_events=2)
        log.record("STARTUP")
        log.record("READINESS_OK")
        log.record("MESSAGE_ACCEPTED")
        self.assertEqual(len(log.snapshot()), 2)
        self.assertEqual(log.snapshot()[0].event_type, "READINESS_OK")


if __name__ == "__main__":
    unittest.main()
