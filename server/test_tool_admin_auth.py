import unittest

from server.tool_admin_auth import ADMIN_PRINCIPAL, authenticate_tool_admin


class ToolAdminAuthTest(unittest.TestCase):
    def test_admin_auth_requires_bearer_header(self):
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            authenticate_tool_admin({}, expected_token="a" * 40)

    def test_admin_auth_rejects_wrong_token(self):
        with self.assertRaisesRegex(PermissionError, "tool_admin_forbidden"):
            authenticate_tool_admin(
                {"Authorization": "Bearer " + ("b" * 40)},
                expected_token="a" * 40,
            )

    def test_admin_auth_rejects_weak_or_missing_configuration(self):
        with self.assertRaisesRegex(PermissionError, "tool_admin_not_configured"):
            authenticate_tool_admin({"Authorization": "Bearer " + ("a" * 40)}, expected_token=None)
        with self.assertRaisesRegex(PermissionError, "tool_admin_not_configured"):
            authenticate_tool_admin({"Authorization": "Bearer short"}, expected_token="short")

    def test_admin_auth_returns_separate_admin_principal(self):
        token = "private-admin-token-" + ("x" * 32)
        principal = authenticate_tool_admin({"Authorization": "Bearer " + token}, token)
        self.assertEqual(principal, ADMIN_PRINCIPAL)
        self.assertNotEqual(principal, "AI-01")


if __name__ == "__main__":
    unittest.main()
