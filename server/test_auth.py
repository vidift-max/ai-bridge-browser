import unittest

from server.auth import Authenticator


class AuthTest(unittest.TestCase):
    def test_valid_token_maps_to_ai(self):
        auth = Authenticator({"token-a": "AI-A"})
        self.assertEqual(auth.authenticate("token-a").ai_id, "AI-A")

    def test_missing_token_rejected(self):
        auth = Authenticator({"token-a": "AI-A"})
        with self.assertRaises(PermissionError):
            auth.authenticate("")

    def test_unknown_token_rejected(self):
        auth = Authenticator({"token-a": "AI-A"})
        with self.assertRaises(PermissionError):
            auth.authenticate("unknown")

    def test_rotation_invalidates_old_credential(self):
        auth = Authenticator({"old": "AI-A"})
        auth.rotate("old", "new")
        with self.assertRaises(PermissionError):
            auth.authenticate("old")
        self.assertEqual(auth.authenticate("new").ai_id, "AI-A")
        self.assertEqual(auth.credential_status("old"), "ROTATED")

    def test_authenticated_principal_contains_current_generation(self):
        auth = Authenticator({"old": "AI-A"})
        first = auth.authenticate("old")
        self.assertEqual((first.ai_id, first.credential_generation), ("AI-A", 1))
        auth.rotate("old", "new")
        second = auth.authenticate("new")
        self.assertEqual((second.ai_id, second.credential_generation), ("AI-A", 2))


if __name__ == "__main__":
    unittest.main()
