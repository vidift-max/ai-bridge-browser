"""CI guardrails for the M130 secure guest-status design (not runtime implementation)."""
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "MISSION_130_SECURE_GUEST_STATUS_CAPABILITY.md"


class Mission130StatusCapabilityDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SPEC.read_text(encoding="utf-8")

    def test_separate_capability_is_required_and_application_id_is_not_auth(self):
        self.assertIn("256-bit", self.spec)
        self.assertIn("applicationId` as authorization", self.spec)
        self.assertIn("not an authentication factor", self.spec)

    def test_digest_only_storage_and_expiry_are_required(self):
        self.assertIn("SHA-256 digest storage only", self.spec)
        self.assertIn("7 days", self.spec)
        self.assertIn("status_capability_expires_at", self.spec)

    def test_lookup_uses_post_and_body_not_url(self):
        self.assertIn("POST /v1/guest-applications/status", self.spec)
        self.assertIn("rather than query strings", self.spec)
        self.assertIn("do not put it in the invite URL", self.spec)

    def test_response_excludes_sensitive_application_and_identity_data(self):
        for forbidden in ("display name", "provider claim", "administrator identity",
                          "AI identity", "membership details", "session tokens"):
            self.assertIn(forbidden, self.spec)

    def test_capability_is_read_only_and_cannot_grant_access(self):
        self.assertIn("cannot be exchanged for a guest session", self.spec)
        self.assertIn("APPROVED_AWAITING_PROVISIONING` is not access", self.spec)

    def test_duplicate_submission_semantics_are_an_explicit_blocker(self):
        self.assertIn("duplicate-submission semantics before returning a token", self.spec)
        self.assertIn("unrecoverable secret", self.spec)

    def test_mission_does_not_claim_endpoint_or_runtime_implementation(self):
        self.assertIn("no endpoint or schema change is implemented", self.spec)
        self.assertIn("No status endpoint", self.spec)


if __name__ == "__main__":
    unittest.main()
