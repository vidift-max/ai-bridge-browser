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
            "status": "BLOCKED",
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
        self.catalog["tools"][0].update({"status": "READY", "enabled": True,
                                         "inputSchemaRef": "registry/tool-hub/schemas/duration_timer.input.schema.json",
                                         "outputSchemaRef": "registry/tool-hub/schemas/duration_timer.output.schema.json"})
        self.catalog["status"] = "PARTIALLY_BLOCKED"
        self.write_catalog()
        service = ToolHubService(self.path, self.permissions)
        self.assertEqual([x["toolId"] for x in service.discover("AI-A")["tools"]], ["duration_timer"])
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

    def test_ready_tool_executes_clean_room_adapter_after_authorization(self):
        self.catalog["tools"][0].update({
            "status": "READY", "enabled": True,
            "inputSchemaRef": "registry/tool-hub/schemas/duration_timer.input.schema.json",
            "outputSchemaRef": "registry/tool-hub/schemas/duration_timer.output.schema.json",
        })
        self.catalog["status"] = "PARTIALLY_BLOCKED"
        self.write_catalog()
        service = ToolHubService(self.path, self.permissions)
        result = service.invoke("AI-A", "duration_timer", {
            "requestId": "123e4567-e89b-42d3-a456-426614174000",
            "toolVersion": "0.0.0", "input": {"duration": "2m"}
        })
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["result"]["seconds"], 120)

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



    def test_catalog_rejects_enabled_blocked_tool(self):
        self.catalog["tools"][0]["enabled"] = True
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "blocked_tool_must_not_be_enabled"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_ready_tool_without_schema_references(self):
        self.catalog["tools"][0].update({"status": "READY", "enabled": True})
        self.catalog["status"] = "PARTIALLY_BLOCKED"
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "ready_tool_requires_schemas"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_schema_path_traversal(self):
        self.catalog["tools"][0].update({
            "status": "READY", "enabled": True,
            "inputSchemaRef": "../outside.schema.json",
            "outputSchemaRef": "schemas/output.schema.json",
        })
        self.catalog["status"] = "PARTIALLY_BLOCKED"
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "ready_tool_requires_schemas"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_inconsistent_top_level_status(self):
        self.catalog["status"] = "READY"
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "catalog_status_mismatch"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_non_object_document_and_invalid_version(self):
        self.path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid_tool_catalog"):
            ToolHubService(self.path, self.permissions)
        self.catalog["catalogVersion"] = 2
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "unsupported_tool_catalog_version"):
            ToolHubService(self.path, self.permissions)


    def test_catalog_rejects_malformed_semantic_version(self):
        self.catalog["tools"][0]["version"] = "1.2"
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "invalid_tool_version"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_wrong_permission_contract(self):
        self.catalog["tools"][0]["requiredPermission"] = "SEND_MESSAGE"
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "invalid_tool_permission_contract"):
            ToolHubService(self.path, self.permissions)

    def test_catalog_rejects_oversized_or_non_string_description(self):
        self.catalog["tools"][0]["description"] = "x" * 241
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "invalid_tool_description"):
            ToolHubService(self.path, self.permissions)
        self.catalog["tools"][0]["description"] = None
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "invalid_tool_description"):
            ToolHubService(self.path, self.permissions)


    def test_catalog_rejects_duplicate_json_object_keys(self):
        self.path.write_text(
            '{"catalogVersion":1,"catalogVersion":1,"status":"BLOCKED","tools":[]}',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate_tool_catalog_key"):
            ToolHubService(self.path, self.permissions)

if __name__ == "__main__":
    unittest.main()
