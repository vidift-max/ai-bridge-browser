import os
import tempfile
import unittest
from pathlib import Path


class StagingActivationContractTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    BLUEPRINT = ROOT / "render.staging.yaml"

    def test_blueprint_uses_free_ephemeral_storage_and_expected_identity_pair(self):
        text = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertIn("name: ai-bridge-browser-staging", text)
        self.assertIn("MESSENGER_AI_ID_A", text)
        self.assertIn("value: AI-USER", text)
        self.assertIn("MESSENGER_AI_ID_B", text)
        self.assertIn("value: AI-PEER", text)
        self.assertIn("MESSENGER_STORAGE_MODE", text)
        self.assertIn("plan: free", text)
        self.assertIn("value: ephemeral", text)
        self.assertIn("MESSENGER_DB_PATH", text)
        self.assertIn("value: ':memory:'", text)


    def test_staging_blueprint_routes_two_distinct_providers_and_keeps_calls_off(self):
        text = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertIn("value: '{\"AI-USER\":\"openai\",\"AI-PEER\":\"anthropic\"}'", text)
        for key in ("AI_PROVIDER_HOST_HMAC_KEY_HEX", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            self.assertIn(f"key: {key}\\n        sync: false", text)
        self.assertIn("key: OPENAI_API_CALLS_ENABLED\\n        value: 'false'", text)
        self.assertIn("key: ANTHROPIC_API_CALLS_ENABLED\\n        value: 'false'", text)

    def test_staging_contract_rejects_paid_or_persistent_storage(self):
        blueprint = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertNotIn("plan: starter", blueprint.lower())
        self.assertNotIn("mountpath: /var/data", blueprint.lower())

    def test_staging_secrets_are_not_hardcoded(self):
        blueprint = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertIn("key: MESSENGER_TOKEN_AI_A\n        sync: false", blueprint)
        self.assertIn("key: MESSENGER_TOKEN_AI_B\n        sync: false", blueprint)
        self.assertNotIn("token-a", blueprint.lower())
        self.assertNotIn("token-b", blueprint.lower())

    def test_runtime_contract_matches_blueprint_without_network(self):
        old = {key: os.environ.get(key) for key in (
            "MESSENGER_STORAGE_MODE",
            "MESSENGER_PERSISTENT_STORAGE_ROOT",
            "MESSENGER_DB_PATH",
        )}
        try:
            with tempfile.TemporaryDirectory() as root:
                os.environ["MESSENGER_STORAGE_MODE"] = "ephemeral"
                os.environ.pop("MESSENGER_PERSISTENT_STORAGE_ROOT", None)
                os.environ["MESSENGER_DB_PATH"] = ":memory:"
                self.assertEqual(os.environ["MESSENGER_STORAGE_MODE"], "ephemeral")
                self.assertEqual(os.environ["MESSENGER_DB_PATH"], ":memory:")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
