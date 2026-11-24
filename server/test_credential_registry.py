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

    def test_authentication_returns_identity_and_generation_atomically(self):
        ai_id, generation = self.registry.authenticate_with_generation("token-a")
        self.assertEqual(ai_id, "AI-A")
        self.assertEqual(generation, 1)
        self.registry.rotate("token-a", "token-a-next")
        with self.assertRaises(PermissionError):
            self.registry.authenticate_with_generation("token-a")
        self.assertEqual(
            self.registry.authenticate_with_generation("token-a-next"),
            ("AI-A", 2))


if __name__ == "__main__":
    unittest.main()
