import unittest

from server.staging_evidence_collector import (
    ALLOWED_FIELDS,
    collect_staging_evidence,
    validate_collected_report,
)


class StagingEvidenceCollectorTest(unittest.TestCase):
    def source(self, **changes):
        value = dict(
            deployment_id="deploy-188",
            environment="staging",
            service_id="service-staging",
            staging_url="https://staging.example.test",
            deployed_commit="approved-sha",
            artifact_sha256="b" * 64,
            deployed_at="2026-11-26T04:00:00Z",
            health_checked_at="2026-11-26T04:02:00Z",
            health_status_code=204,
            health_check_passed=True,
            rollback_commit="rollback-sha",
            rollback_target_verified=True,
            operator_approved=True,
            production_target=False,
            secrets_included=False,
        )
        value.update(changes)
        return value

    def collect(self, source):
        return collect_staging_evidence(source, expected_commit="approved-sha")

    def test_complete_allowlisted_evidence_is_collected_and_valid(self):
        report = self.collect(self.source())
        self.assertEqual(report["state"], "READY_FOR_STAGING_HANDOFF_REVIEW")
        self.assertTrue(report["ready"])
        self.assertEqual(set(report["evidence"]), ALLOWED_FIELDS)
        self.assertTrue(validate_collected_report(report))
        self.assertFalse(report["liveTestAuthorized"])
        self.assertFalse(report["deploymentPerformed"])
        self.assertFalse(report["healthProbePerformed"])
        self.assertFalse(report["rollbackPerformed"])
        self.assertFalse(report["providerCallsPerformed"])

    def test_unknown_secret_fields_are_discarded_not_echoed(self):
        raw = self.source(
            OPENAI_API_KEY="sk-live-do-not-echo",
            bearer_token="Bearer do-not-echo",
            cookie="session=do-not-echo",
            nested={"ANTHROPIC_API_KEY": "do-not-echo"},
        )
        report = self.collect(raw)
        rendered = repr(report)
        for secret in ("sk-live-do-not-echo", "Bearer do-not-echo",
                       "session=do-not-echo", "do-not-echo"):
            self.assertNotIn(secret, rendered)
        self.assertEqual(report["unknownFieldCount"], 4)
        self.assertFalse(report["secretsIncludedInReport"])
        self.assertFalse(report["rawInputIncluded"])

    def test_missing_or_mismatched_values_remain_blocked(self):
        for changes in (
            {"deployed_commit": "old-sha"},
            {"staging_url": "http://staging.example.test"},
            {"health_status_code": 503},
            {"rollback_target_verified": False},
        ):
            self.assertEqual(self.collect(self.source(**changes))["state"], "BLOCKED")

    def test_wrong_input_type_rejected(self):
        with self.assertRaises(TypeError):
            collect_staging_evidence(["not", "a", "mapping"],
                                     expected_commit="approved-sha")

    def test_fingerprint_is_deterministic(self):
        first = self.collect(self.source())
        second = self.collect(dict(reversed(list(self.source().items()))))
        self.assertEqual(first["evidenceFingerprintSha256"],
                         second["evidenceFingerprintSha256"])

    def test_report_tampering_is_detected(self):
        report = self.collect(self.source())
        report["evidence"]["deployment_id"] = "altered"
        self.assertFalse(validate_collected_report(report))

    def test_forbidden_report_flags_fail_validation(self):
        report = self.collect(self.source())
        report["liveTestAuthorized"] = True
        self.assertFalse(validate_collected_report(report))

    def test_extra_output_fields_fail_validation(self):
        report = self.collect(self.source())
        report["evidence"]["provider_api_key"] = "not-allowed"
        self.assertFalse(validate_collected_report(report))


if __name__ == "__main__":
    unittest.main()
