import unittest

from server.credential_registry import CredentialRegistry


class CredentialRegistryTest(unittest.TestCase):
    def setUp(self):
        self.registry = CredentialRegistry({"token-a": "AI-A", "token-b": "AI-B"})

    def test_active_credential_authenticates(self):
        self.assertEqual(self.registry.authenticate("token-a"), "AI-A")
        self.assertEqual(self.registry.status("token-a"), "ACTIVE")

    def test_revoked_credential_is_rejected(self):
        self.registry.revoke("token-a")
        self.assertEqual(self.registry.status("token-a"), "REVOKED")
        with self.assertRaises(PermissionError):
            self.registry.authenticate("token-a")

    def test_unknown_credential_is_rejected(self):
        self.assertEqual(self.registry.status("missing"), "UNKNOWN")
        with self.assertRaises(PermissionError):
            self.registry.authenticate("missing")

    def test_revoke_unknown_credential_fails(self):
        with self.assertRaises(KeyError):
            self.registry.revoke("missing")


if __name__ == "__main__":
    unittest.main()
