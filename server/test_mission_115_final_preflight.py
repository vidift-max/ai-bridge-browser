import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_first_contact_preflight import preflight


ENV = {
    "MESSENGER_TOKEN_AI_A": "synthetic-token-a",
    "MESSENGER_TOKEN_AI_B": "synthetic-token-b",
    "MESSENGER_AI_ID_A": "AI-01",
    "MESSENGER_AI_ID_B": "AI-02",
    "MESSENGER_ENVIRONMENT": "staging",
    "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
    "MESSENGER_STORAGE_MODE": "ephemeral",
    "MESSENGER_DB_PATH": ":memory:",
    "MESSENGER_FIRST_CONTACT_OPERATION_ID": "mission115-op-0001",
}


class Mission115FinalPreflightTest(unittest.TestCase):
    def test_valid_configuration_passes_without_network_or_execution(self):
        result = preflight("https://stage.example", "room-115", ENV.copy())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["realContact"], "NOT_AUTHORIZED")
        self.assertEqual(result["execution"], "NOT_STARTED")
        self.assertNotIn("synthetic-token", str(result))
        self.assertNotIn("stage.example", str(result))

    def test_wrong_environment_or_storage_fails_closed(self):
        for key, value in (
            ("MESSENGER_ENVIRONMENT", "production"),
            ("MESSENGER_ALLOW_EPHEMERAL_STAGING", "false"),
            ("MESSENGER_STORAGE_MODE", "persistent"),
            ("MESSENGER_DB_PATH", "/var/data/messages.sqlite"),
        ):
            env = ENV.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "staging_configuration_invalid"):
                preflight("https://stage.example", "room-115", env)

    def test_invalid_operation_id_fails_closed(self):
        env = ENV.copy()
        env["MESSENGER_FIRST_CONTACT_OPERATION_ID"] = "short"
        with self.assertRaisesRegex(ValueError, "valid_operation_id_required"):
            preflight("https://stage.example", "room-115", env)

    def test_missing_or_duplicate_credentials_fail_closed(self):
        for key, value in (("MESSENGER_TOKEN_AI_A", ""), ("MESSENGER_TOKEN_AI_B", "synthetic-token-a")):
            env = ENV.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                preflight("https://stage.example", "room-115", env)

    def test_execution_authorization_is_not_granted_by_preflight(self):
        env = ENV.copy()
        env["MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED"] = "true"
        env["MESSENGER_FIRST_CONTACT_EXECUTE"] = "true"
        result = preflight("https://stage.example", "room-115", env)
        self.assertEqual(result["realContact"], "NOT_AUTHORIZED")
        self.assertEqual(result["execution"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
