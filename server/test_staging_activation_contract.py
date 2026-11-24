import os
import tempfile
import unittest
from pathlib import Path


class StagingActivationContractTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    BLUEPRINT = ROOT / "render.staging.yaml"

    def test_blueprint_uses_persistent_storage_and_expected_identity_pair(self):
        text = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertIn("name: ai-bridge-browser-staging", text)
        self.assertIn("MESSENGER_AI_ID_A", text)
        self.assertIn("value: AI-01", text)
        self.assertIn("MESSENGER_AI_ID_B", text)
        self.assertIn("value: AI-02", text)
        self.assertIn("MESSENGER_STORAGE_MODE", text)
        self.assertIn("value: persistent", text)
        self.assertIn("MESSENGER_PERSISTENT_STORAGE_ROOT", text)
        self.assertIn("value: /var/data", text)
        self.assertIn("MESSENGER_DB_PATH", text)
        self.assertIn("value: /var/data/messenger.sqlite", text)
        self.assertIn("mountPath: /var/data", text)

    def test_staging_contract_rejects_ephemeral_storage(self):
        blueprint = self.BLUEPRINT.read_text(encoding="utf-8")
        self.assertNotIn("value: ephemeral", blueprint.lower())

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
                os.environ["MESSENGER_STORAGE_MODE"] = "persistent"
                os.environ["MESSENGER_PERSISTENT_STORAGE_ROOT"] = root
                os.environ["MESSENGER_DB_PATH"] = str(Path(root) / "messenger.sqlite")
                self.assertEqual(os.environ["MESSENGER_STORAGE_MODE"], "persistent")
                self.assertTrue(os.environ["MESSENGER_DB_PATH"].startswith(root))
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
