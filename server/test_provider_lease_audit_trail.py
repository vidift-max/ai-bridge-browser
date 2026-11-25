import unittest

from server.sqlite_store import SQLiteMessengerStore


class ProviderLeaseAuditTrailTests(unittest.TestCase):
    def setUp(self):
        self.store = SQLiteMessengerStore(":memory:")

    def tearDown(self):
        self.store.close()

    def events(self, request_id):
        return self.store.list_provider_request_audit_events("AI-AUDIT", request_id)

    def test_schema_v15_records_claim_recovery_renewal_failure_and_retry(self):
        self.assertEqual(
            self.store.connection.execute(
                "SELECT value FROM schema_meta WHERE key='version'"
            ).fetchone()["value"],
            "15",
        )
        _, outcome = self.store.claim_provider_request(
            "AI-AUDIT", "audit-lifecycle", "digest", "room", "AI-AUDIT",
            100.0, lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")
        _, outcome = self.store.claim_provider_request(
            "AI-AUDIT", "audit-lifecycle", "digest", "room", "AI-AUDIT",
            130.0, lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")
        self.assertTrue(self.store.renew_provider_request_lease(
            "AI-AUDIT", "audit-lifecycle", "digest", 2, 131.0, lease_seconds=30.0))
        self.assertTrue(self.store.fail_provider_request(
            "AI-AUDIT", "audit-lifecycle", "digest", "provider_unavailable", 132.0, 2))
        _, outcome = self.store.claim_provider_request(
            "AI-AUDIT", "audit-lifecycle", "digest", "room", "AI-AUDIT",
            133.0, lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")

        rows = self.events("audit-lifecycle")
        self.assertEqual(
            [row["event_type"] for row in rows],
            ["CLAIMED", "RECOVERED", "LEASE_RENEWED", "FAILED", "RETRIED"],
        )
        self.assertEqual([row["attempt_generation"] for row in rows], [1, 2, 2, 2, 3])
        self.assertEqual(rows[0]["from_status"], None)
        self.assertEqual(rows[0]["to_status"], "PROCESSING")
        self.assertEqual(rows[1]["from_status"], "PROCESSING")
        self.assertEqual(rows[3]["error_code"], "provider_unavailable")
        self.assertEqual(rows[4]["from_status"], "FAILED")

    def test_completion_event_is_committed_with_request_completion(self):
        self.store.claim_provider_request(
            "AI-AUDIT", "audit-complete", "digest", "room", "AI-AUDIT",
            10.0, lease_seconds=30.0)
        result = self.store.complete_provider_request(
            "AI-AUDIT", "audit-complete", "digest", "response",
            "fake-provider", "fake-model",
            {"statement": {"providerId": "fake-provider"}, "signature": "sig",
             "algorithm": "HMAC-SHA256"},
            "message-audit", 11.0, attempt_generation=1, lease_seconds=30.0)
        self.assertEqual(result["status"], "COMPLETED")
        rows = self.events("audit-complete")
        self.assertEqual([row["event_type"] for row in rows], ["CLAIMED", "COMPLETED"])
        self.assertEqual(rows[-1]["from_status"], "PROCESSING")
        self.assertEqual(rows[-1]["to_status"], "COMPLETED")
        self.assertEqual(rows[-1]["attempt_generation"], 1)

    def test_audit_events_are_isolated_by_principal_and_request(self):
        self.store.claim_provider_request(
            "AI-AUDIT", "same-request", "digest", "room", "AI-AUDIT", 1.0)
        self.store.claim_provider_request(
            "AI-OTHER", "same-request", "digest", "room", "AI-OTHER", 1.0)
        self.assertEqual(len(self.store.list_provider_request_audit_events(
            "AI-AUDIT", "same-request")), 1)
        self.assertEqual(len(self.store.list_provider_request_audit_events(
            "AI-OTHER", "same-request")), 1)
        self.assertEqual(self.store.list_provider_request_audit_events(
            "AI-AUDIT", "missing-request"), [])

    def test_audit_query_limit_is_bounded_and_rejects_invalid_values(self):
        for value in (0, 501, True, 1.5, "10"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_provider_audit_limit"):
                    self.store.list_provider_request_audit_events(
                        "AI-AUDIT", "any-request", value)
        self.store.claim_provider_request(
            "AI-AUDIT", "limited", "digest", "room", "AI-AUDIT", 1.0)
        self.assertEqual(len(self.store.list_provider_request_audit_events(
            "AI-AUDIT", "limited", 1)), 1)


if __name__ == "__main__":
    unittest.main()
