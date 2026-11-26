import unittest

from server.staging_verification_adapter import (
    adapt_staging_verification,
    canonical_record_sha256,
    validate_staging_verification_report,
)


class StagingVerificationAdapterTest(unittest.TestCase):
    COMMIT = "a" * 40
    SERVICE = "svc-staging-189"
    URL = "https://staging.example.test"

    def source(self, **changes):
        record = {
            "environment": "staging",
            "service_id": self.SERVICE,
            "staging_url": self.URL,
            "verified_commit": self.COMMIT,
            "artifact_sha256": "b" * 64,
            "checked_at": "2026-11-26T04:00:00Z",
            "health_status_code": 204,
            "health_check_passed": True,
            "verifier_identity": "operator-verified-run-189",
            "source_kind": "operator_supplied",
            "probe_execution_claimed": False,
        }
        record.update(changes)
        record["source_record_sha256"] = canonical_record_sha256(record)
        return record

    def adapt(self, record):
        return adapt_staging_verification(
            record,
            expected_commit=self.COMMIT,
            expected_service_id=self.SERVICE,
            expected_staging_url=self.URL,
        )

    def test_valid_operator_record_is_matched_but_unattested(self):
        report = self.adapt(self.source())
        self.assertEqual(report["state"], "MATCHED_UNATTESTED")
        self.assertTrue(report["matched"])
        self.assertTrue(validate_staging_verification_report(report))
        self.assertFalse(report["sourceAuthenticityVerified"])
        self.assertFalse(report["probePerformedByAdapter"])
        self.assertFalse(report["liveTestAuthorized"])

    def test_service_identity_mismatch_blocks(self):
        report = self.adapt(self.source(service_id="other-service"))
        self.assertEqual(report["state"], "BLOCKED")
        self.assertFalse(report["checks"]["serviceIdentityMatches"])

    def test_commit_mismatch_blocks(self):
        report = self.adapt(self.source(verified_commit="c" * 40))
        self.assertFalse(report["matched"])

    def test_non_https_or_credential_url_blocks(self):
        for url in ("http://staging.example.test",
                    "https://user:pass@staging.example.test",
                    "https://staging.example.test/?token=secret"):
            report = self.adapt(self.source(staging_url=url))
            self.assertFalse(report["checks"]["stagingUrlMatches"])

    def test_bool_and_string_http_status_are_rejected(self):
        for status in (True, "204", 500):
            report = self.adapt(self.source(health_status_code=status))
            self.assertFalse(report["checks"]["healthStatusIs2xxInteger"])

    def test_naive_timestamp_and_failed_health_block(self):
        report = self.adapt(self.source(
            checked_at="2026-11-26T04:00:00",
            health_check_passed=False,
        ))
        self.assertFalse(report["checks"]["timestampIsTimezoneAware"])
        self.assertFalse(report["checks"]["healthCheckPassed"])

    def test_digest_tampering_is_detected(self):
        record = self.source()
        record["service_id"] = "tampered"
        report = self.adapt(record)
        self.assertFalse(report["checks"]["sourceRecordDigestMatches"])

    def test_unknown_secret_fields_are_discarded(self):
        record = self.source()
        record["OPENAI_API_KEY"] = "sk-secret-not-for-report"
        record["cookie"] = "session=secret"
        report = self.adapt(record)
        self.assertNotIn("sk-secret-not-for-report", repr(report))
        self.assertNotIn("session=secret", repr(report))
        self.assertEqual(report["unknownFieldCount"], 2)

    def test_probe_claim_must_match_source_kind(self):
        operator = self.adapt(self.source(probe_execution_claimed=True))
        self.assertFalse(operator["checks"]["operatorRecordDoesNotClaimAdapterProbe"])
        automated = self.adapt(self.source(
            source_kind="automated_probe_record",
            probe_execution_claimed=True,
        ))
        self.assertTrue(automated["checks"]["automatedProbeClaimPresent"])

    def test_report_tampering_and_false_flags_are_rejected(self):
        report = self.adapt(self.source())
        report["record"]["service_id"] = "changed"
        self.assertFalse(validate_staging_verification_report(report))
        report = self.adapt(self.source())
        report["probePerformedByAdapter"] = True
        self.assertFalse(validate_staging_verification_report(report))

    def test_wrong_input_type_rejected(self):
        with self.assertRaises(TypeError):
            self.adapt(["not", "a", "mapping"])

    def test_unsafe_url_and_verifier_values_are_redacted_from_report(self):
        for unsafe in (
            "https://user:password@staging.example.test",
            "https://staging.example.test/private/token-value",
        ):
            report = self.adapt(self.source(staging_url=unsafe))
            self.assertNotIn("password", repr(report))
            self.assertNotIn("token-value", repr(report))
            self.assertEqual(report["record"]["staging_url"], "[REDACTED]")
        report = self.adapt(self.source(verifier_identity="Bearer sk-secret-value"))
        self.assertNotIn("sk-secret-value", repr(report))
        self.assertEqual(report["record"]["verifier_identity"], "[REDACTED]")

    def test_automated_probe_record_requires_explicit_claim(self):
        report = self.adapt(self.source(
            source_kind="automated_probe_record",
            probe_execution_claimed=False,
        ))
        self.assertFalse(report["checks"]["automatedProbeClaimPresent"])
        self.assertEqual(report["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
