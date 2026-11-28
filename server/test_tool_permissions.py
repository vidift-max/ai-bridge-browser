import unittest

from server.tool_permissions import SUPPORTED_TOOL_IDS, ToolPermissionRegistry


class ToolPermissionRegistryTest(unittest.TestCase):
    def test_missing_grant_denies_by_default(self):
        registry = ToolPermissionRegistry()
        self.assertFalse(registry.can_use("AI-01", "duration_timer"))
        with self.assertRaisesRegex(PermissionError, "tool_use_forbidden"):
            registry.require("AI-01", "duration_timer")

    def test_grant_is_scoped_to_exact_principal_and_tool(self):
        registry = ToolPermissionRegistry({"AI-01": ["duration_timer"]})
        self.assertTrue(registry.can_use("AI-01", "duration_timer"))
        self.assertFalse(registry.can_use("AI-02", "duration_timer"))
        self.assertFalse(registry.can_use("AI-01", "recipe_scaler"))

    def test_all_five_catalog_tools_are_known_but_not_implicitly_granted(self):
        self.assertEqual(len(SUPPORTED_TOOL_IDS), 5)
        registry = ToolPermissionRegistry()
        for tool_id in SUPPORTED_TOOL_IDS:
            self.assertFalse(registry.can_use("AI-01", tool_id))

    def test_unknown_tool_is_not_found(self):
        registry = ToolPermissionRegistry({"AI-01": ["duration_timer"]})
        with self.assertRaisesRegex(LookupError, "tool_not_found"):
            registry.require("AI-01", "arbitrary_tool")

    def test_missing_principal_requires_authentication(self):
        registry = ToolPermissionRegistry({"AI-01": ["duration_timer"]})
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            registry.require("", "duration_timer")

    def test_unsupported_grant_is_rejected_at_configuration_time(self):
        with self.assertRaisesRegex(ValueError, "unsupported_tool_permission"):
            ToolPermissionRegistry({"AI-01": ["shell_exec"]})

    def test_principal_identifiers_must_be_canonical_strings(self):
        with self.assertRaisesRegex(ValueError, "invalid_tool_permission_principal"):
            ToolPermissionRegistry({" AI-01": ["duration_timer"]})

    def test_permitted_tool_ids_are_immutable_and_empty_for_unknown_principal(self):
        registry = ToolPermissionRegistry({"AI-01": ["duration_timer"]})
        self.assertEqual(registry.permitted_tool_ids("AI-01"), frozenset({"duration_timer"}))
        self.assertEqual(registry.permitted_tool_ids("AI-99"), frozenset())
        with self.assertRaises(AttributeError):
            registry.permitted_tool_ids("AI-01").add("quiz_engine")


if __name__ == "__main__":
    unittest.main()
