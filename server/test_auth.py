import unittest
from server.auth import Authenticator

class AuthenticatorTest(unittest.TestCase):
    def setUp(self):
        self.auth=Authenticator({"token-a":"AI-A","token-b":"AI-B"})

    def test_valid_token_maps_to_principal(self):
        self.assertEqual(self.auth.authenticate("token-a").ai_id,"AI-A")

    def test_missing_token_rejected(self):
        with self.assertRaises(PermissionError):
            self.auth.authenticate("")

    def test_unknown_token_rejected(self):
        with self.assertRaises(PermissionError):
            self.auth.authenticate("wrong")

    def test_revoked_token_rejected(self):
        self.auth.revoke("token-a")
        with self.assertRaises(PermissionError):
            self.auth.authenticate("token-a")
        self.assertEqual(self.auth.credential_status("token-a"),"REVOKED")

if __name__=="__main__":
    unittest.main()
