"""CI guardrails for the M131 duplicate/status capability contract."""
from pathlib import Path
import unittest


class Mission131DuplicateStatusCapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = Path("docs/MISSION_131_DUPLICATE_STATUS_CAPABILITY_CONTRACT.md").read_text()

    def test_client_capability_is_256_bit_and_tab_memory_only(self):
        self.assertIn("32 cryptographically random bytes", self.doc)
        self.assertIn("crypto.getRandomValues", self.doc)
        self.assertIn("JavaScript variable scoped to the live invite page", self.doc)
        self.assertIn("not placed in the URL", self.doc)
        self.assertIn("localStorage", self.doc)
        self.assertIn("sessionStorage", self.doc)

    def test_digest_only_atomic_persistence_and_expiry(self):
        self.assertIn("SHA-256(capability)", self.doc)
        self.assertIn("status_capability_hash", self.doc)
        self.assertIn("status_capability_expires_at", self.doc)
        self.assertIn("one SQLite transaction", self.doc)
        self.assertIn("7 days", self.doc)
        self.assertIn("never store the plaintext", self.doc)

    def test_duplicate_replay_requires_same_capability(self):
        self.assertIn("matching unexpired capability digest", self.doc)
        self.assertIn("idempotent replay", self.doc)
        self.assertIn("different/missing capability", self.doc)
        self.assertIn("do not increment invite uses", self.doc)
        self.assertIn("Legacy rows with NULL capability digest", self.doc)

    def test_status_lookup_never_uses_application_id_as_auth(self):
        self.assertIn("POST /v1/guest-applications/status", self.doc)
        self.assertIn("do not accept applicationId as authorization", self.doc)
        self.assertIn("Unknown, expired, and malformed values share a generic not-found response", self.doc)

    def test_public_status_response_is_minimal_and_read_only(self):
        self.assertIn('"state":"..."', self.doc)
        self.assertIn("PENDING", self.doc)
        self.assertIn("APPROVED_AWAITING_PROVISIONING", self.doc)
        self.assertIn("REVOKED", self.doc)
        self.assertIn("Capability is read-only", self.doc)
        self.assertIn("cannot approve, provision, authenticate", self.doc)

    def test_lost_capability_has_no_public_recovery(self):
        self.assertIn("no recovery or rotation through the public endpoint", self.doc)
        self.assertIn("contact the room administrator", self.doc)
        self.assertIn("generic duplicate receipt", self.doc)

    def test_m132_is_implementation_gate_not_a_claim(self):
        self.assertIn("M132 implementation acceptance", self.doc)
        self.assertIn("does not implement schema v10", self.doc)
        self.assertIn("not a working status feature", self.doc)


if __name__ == "__main__":
    unittest.main()
