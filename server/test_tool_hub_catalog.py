import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOL_HUB_ROOT = REPOSITORY_ROOT / "registry" / "tool-hub"
EXPECTED_TOOLS = {
    "duration_timer",
    "recipe_scaler",
    "quiz_engine",
    "svg_chart",
    "link_card",
}


class ToolHubCatalogContractTests(unittest.TestCase):
    def _read_json(self, filename):
        with (TOOL_HUB_ROOT / filename).open(encoding="utf-8") as source:
            return json.load(source)

    def test_catalog_contains_exact_five_expected_tool_ids(self):
        catalog = self._read_json("catalog.json")
        self.assertEqual(
            {tool["toolId"] for tool in catalog["tools"]},
            EXPECTED_TOOLS,
        )
        self.assertEqual(len(catalog["tools"]), 5)

    def test_every_clean_room_tool_is_ready_with_versioned_schemas(self):
        catalog = self._read_json("catalog.json")
        self.assertEqual(catalog["status"], "READY")
        for tool in catalog["tools"]:
            self.assertTrue(tool["enabled"])
            self.assertEqual(tool["status"], "READY")
            self.assertEqual(tool["version"], "1.0.0")
            self.assertEqual(tool["requiredPermission"], "TOOL_USE")
            self.assertTrue((REPOSITORY_ROOT / tool["inputSchemaRef"]).is_file())
            self.assertTrue((REPOSITORY_ROOT / tool["outputSchemaRef"]).is_file())

    def test_all_published_contract_documents_are_valid_json(self):
        for filename in (
            "catalog.json",
            "catalog.schema.json",
            "tool-invocation.schema.json",
            "tool-result.schema.json",
        ):
            with self.subTest(filename=filename):
                self._read_json(filename)

    def test_catalog_schema_allows_ready_only_with_tool_schemas(self):
        schema = self._read_json("catalog.schema.json")
        self.assertEqual(
            schema["$defs"]["tool"]["properties"]["enabled"]["type"],
            "boolean",
        )
        self.assertEqual(len(schema["$defs"]["tool"]["allOf"]), 2)

    def test_invocation_envelope_has_versioned_input_and_strict_fields(self):
        schema = self._read_json("tool-invocation.schema.json")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"requestId", "toolVersion", "input"})
        self.assertEqual(schema["properties"]["input"]["maxProperties"], 64)

    def test_result_contract_has_stable_statuses_and_error_codes(self):
        schema = self._read_json("tool-result.schema.json")
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["SUCCEEDED", "REJECTED", "FAILED", "TIMED_OUT"],
        )
        self.assertIn(
            "TOOL_USE_FORBIDDEN",
            schema["properties"]["error"]["properties"]["code"]["enum"],
        )


if __name__ == "__main__":
    unittest.main()
