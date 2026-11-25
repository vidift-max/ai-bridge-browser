import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_first_contact_authorization import validate_environment


BASE = {
    "MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED": "true",
    "MESSENGER_FIRST_CONTACT_EXECUTE": "true",
    "MESSENGER_ENVIRONMENT": "staging",
    "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
    "MESSENGER_STORAGE_MODE": "ephemeral",
    "MESSENGER_DB_PATH": ":memory:",
    "MESSENGER_AI_ID_A": "AI-01",
    "MESSENGER_AI_ID_B": "AI-02",
    "MESSENGER_TOKEN_AI_A": "synthetic-token-a",
    "MESSENGER_TOKEN_AI_B": "synthetic-token-b",
    "MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN": "https://stage.example",
    "MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID": "room-114",
    "MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID": "m114-operation-0001",
}


class Mission114AuthorizationGateTest(unittest.TestCase):
    def test_valid_explicit_staging_configuration_passes_offline(self):
        result = validate_environment(BASE.copy(), "https://stage.example", "room-114", "m114-operation-0001")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertNotIn("synthetic-token", str(result))

    def test_each_authorization_and_storage_gate_is_mandatory(self):
        for key, value, expected in (
            ("MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED", "false", "explicit_staging_authorization_required"),
            ("MESSENGER_FIRST_CONTACT_EXECUTE", "false", "explicit_execution_gate_required"),
            ("MESSENGER_ENVIRONMENT", "production", "staging_environment_required"),
            ("MESSENGER_ALLOW_EPHEMERAL_STAGING", "false", "ephemeral_staging_opt_in_required"),
            ("MESSENGER_STORAGE_MODE", "persistent", "ephemeral_storage_required"),
            ("MESSENGER_DB_PATH", "/var/data/messages.sqlite", "in_memory_database_required"),
        ):
            env = BASE.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, expected):
                validate_environment(env, "https://stage.example", "room-114", "m114-operation-0001")

    def test_fixed_identities_and_distinct_credentials_are_required(self):
        for key, value in (
            ("MESSENGER_AI_ID_A", "AI-X"),
            ("MESSENGER_AI_ID_B", "AI-X"),
            ("MESSENGER_TOKEN_AI_A", ""),
            ("MESSENGER_TOKEN_AI_B", "synthetic-token-a"),
        ):
            env = BASE.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_environment(env, "https://stage.example", "room-114", "m114-operation-0001")

    def test_missing_authorization_fails_closed(self):
        env = BASE.copy()
        del env["MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED"]
        with self.assertRaisesRegex(ValueError, "explicit_staging_authorization_required"):
            validate_environment(env)


    def test_approval_is_bound_to_exact_origin_conversation_and_operation(self):
        for key, value, expected in (
            ("MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN", "https://other.example", "approved_origin_mismatch"),
            ("MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID", "other-room", "approved_conversation_mismatch"),
            ("MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID", "m114-operation-0002", "approved_operation_mismatch"),
        ):
            env = BASE.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, expected):
                validate_environment(env, "https://stage.example", "room-114", "m114-operation-0001")

    def test_missing_exact_operation_binding_fails_closed(self):
        env = BASE.copy()
        del env["MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID"]
        with self.assertRaisesRegex(ValueError, "approved_operation_mismatch"):
            validate_environment(env, "https://stage.example", "room-114", "m114-operation-0001")


if __name__ == "__main__":
    unittest.main()
