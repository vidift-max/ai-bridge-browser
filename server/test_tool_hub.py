import json
import tempfile
import unittest
from pathlib import Path

from server.tool_permissions import ToolPermissionRegistry
from server.tool_hub import ToolHubService, ToolUnavailable, ToolNotImplemented


class ToolHubServiceTest(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "catalogVersion": 1,
            "tools": [
                {"toolId": tool_id, "version": "0.0.0",
                 "status": "BLOCKED_LICENSE_REVIEW", "enabled": False,
                 "requiredPermission": "TOOL_USE",
                 "inputSchemaRef": None, "outputSchemaRef": None}
                for tool_id in ("duration_timer", "recipe_scaler", "quiz_engine", "svg_chart", "link_card")
            ]
        }
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "catalog.json"
        self.write_catalog()
        self.permissions = ToolPermissionRegistry({
            "AI-A": {"duration_timer", "recipe_scaler"},
            "AI-B": {"quiz_engine"},
        })
        self.service = ToolHubService(self.path, self.permissions)

    def tearDown(self):
        self.temp.cleanup()

    def write_catalog(self):
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")

    def test_discovery_is_empty_for_blocked_catalog_even_with_grant(self):
        self.assertEqual(self.service.discover("AI-A"), {"tools": []})

    def test_discovery_filters_by_exact_principal_grant(self):
        self.catalog["tools"][0].update({"status": "READY", "enabled": True})
        self.write_catalog()
        service = ToolHubService(self.path, self.permissions)
        self.assertEqual([x["toolId"] for x in service.discover("AI-A")], ["duration_timer"])
        self.assertEqual(service.discover("AI-UNKNOWN"), {"tools": []})

    def test_invocation_denies_without_tool_use(self):
        with self.assertRaises(PermissionError):
            self.service.invoke("AI-C", "duration_timer")

    def test_invocation_rejects_unknown_tool(self):
        with self.assertRaises(LookupError):
            self.service.invoke("AI-A", "unknown_tool")

    def test_invocation_rejects_blocked_tool_even_with_grant(self):
        with self.assertRaises(ToolUnavailable):
            self.service.invoke("AI-A", "duration_timer")

    def test_ready_tool_still_has_no_executor(self):
        self.catalog["tools"][0].update({"status": "READY", "enabled": True})
        self.write_catalog()
        service = ToolHubService(self.path, self.permissions)
        with self.assertRaises(ToolNotImplemented):
            service.invoke("AI-A", "duration_timer")

    def test_catalog_must_contain_exact_supported_set(self):
        self.catalog["tools"].pop()
        self.write_catalog()
        with self.assertRaises(ValueError):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_duplicate_or_unknown_ids(self):
        self.catalog["tools"].append(dict(self.catalog["tools"][0]))
        self.write_catalog()
        with self.assertRaises(ValueError):
            ToolHubService(self.path, self.permissions)


if __name__ == "__main__":
    unittest.main()
