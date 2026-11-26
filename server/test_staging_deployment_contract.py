import unittest

from server.staging_deployment_contract import (
    BLOCKED,
    READY_FOR_STAGING_HANDOFF_REVIEW,
    StagingDeploymentEvidence,
    evaluate_staging_deployment,
)


class StagingDeploymentContractTest(unittest.TestCase):
    def evidence(self, **changes):
        values = dict(
            deployment_id="deploy-187-001",
            environment="staging",
            service_id="ai-bridge-staging",
            staging_url="https://staging.example.test",
            deployed_commit="approved-sha",
            artifact_sha256="a" * 64,
            deployed_at="2026-11-26T03:00:00Z",
            health_checked_at="2026-11-26T03:02:00+00:00",
            health_status_code=200,
            health_check_passed=True,
            rollback_commit="known-good-sha",
            rollback_target_verified=True,
            operator_approved=True,
            production_target=False,
            secrets_included=False,
        )
        values.update(changes)
        return StagingDeploymentEvidence(**values)

    def evaluate(self, evidence):
        return evaluate_staging_deployment(evidence, expected_commit="approved-sha")

    def test_complete_evidence_only_ready_for_handoff_review(self):
        result = self.evaluate(self.evidence())
        self.assertEqual(result["state"], READY_FOR_STAGING_HANDOFF_REVIEW)
        self.assertTrue(result["ready"])
        self.assertFalse(result["deploymentPerformed"])
        self.assertFalse(result["healthProbePerformed"])
        self.assertFalse(result["rollbackPerformed"])
        self.assertFalse(result["providerCallsPerformed"])
        self.assertFalse(result["secretsRead"])
        self.assertFalse(result["secretsStored"])
        self.assertFalse(result["liveTestAuthorized"])

    def test_empty_evidence_is_blocked(self):
        self.assertEqual(self.evaluate(StagingDeploymentEvidence())["state"], BLOCKED)

    def test_production_or_non_staging_target_is_blocked(self):
        for changes in ({"environment": "production"},
                        {"production_target": True}):
            self.assertEqual(self.evaluate(self.evidence(**changes))["state"], BLOCKED)

    def test_missing_deployment_or_service_identity_is_blocked(self):
        for changes in ({"deployment_id": ""}, {"service_id": ""}):
            self.assertEqual(self.evaluate(self.evidence(**changes))["state"], BLOCKED)

    def test_non_https_or_credential_bearing_url_is_blocked(self):
        for url in ("http://staging.example.test",
                    "https://user:pass@staging.example.test",
                    "https://staging.example.test/path?token=x",
                    "https://staging.example.test/#fragment"):
            self.assertEqual(self.evaluate(self.evidence(staging_url=url))["state"], BLOCKED)

    def test_commit_must_match_exactly(self):
        self.assertEqual(self.evaluate(self.evidence(deployed_commit="stale-sha"))["state"], BLOCKED)

    def test_artifact_digest_must_be_sha256_hex(self):
        for digest in ("", "z" * 64, "a" * 63, "a" * 65):
            self.assertEqual(self.evaluate(self.evidence(artifact_sha256=digest))["state"], BLOCKED)

    def test_timestamps_must_be_aware_and_ordered(self):
        for changes in (
            {"deployed_at": "2026-11-26T03:00:00"},
            {"health_checked_at": "2026-11-26T03:02:00"},
            {"health_checked_at": "2026-11-26T02:59:00Z"},
        ):
            self.assertEqual(self.evaluate(self.evidence(**changes))["state"], BLOCKED)

    def test_health_requires_true_2xx_non_boolean_status(self):
        for status in (0, 199, 300, True, "200"):
            self.assertEqual(self.evaluate(self.evidence(health_status_code=status))["state"], BLOCKED)
        self.assertEqual(self.evaluate(self.evidence(health_check_passed=False))["state"], BLOCKED)

    def test_rollback_must_be_distinct_and_verified(self):
        for changes in (
            {"rollback_commit": ""},
            {"rollback_commit": "approved-sha"},
            {"rollback_target_verified": False},
        ):
            self.assertEqual(self.evaluate(self.evidence(**changes))["state"], BLOCKED)

    def test_operator_approval_and_secret_hygiene_are_mandatory(self):
        for changes in ({"operator_approved": False}, {"secrets_included": True}):
            self.assertEqual(self.evaluate(self.evidence(**changes))["state"], BLOCKED)


if __name__ == "__main__":
    unittest.main()
