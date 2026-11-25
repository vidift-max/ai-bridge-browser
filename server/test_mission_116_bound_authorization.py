import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_first_contact_authorization import validate_environment


ENV = {
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
    "MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID": "room-116",
    "MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID": "m116-operation-0001",
}


class Mission116BoundAuthorizationTest(unittest.TestCase):
    def test_exact_binding_passes_without_network(self):
        result = validate_environment(ENV.copy(), "https://stage.example",
                                      "room-116", "m116-operation-0001")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertNotIn("synthetic-token", str(result))
        self.assertNotIn("stage.example", str(result))
        self.assertNotIn("m116-operation", str(result))

    def test_each_binding_mismatch_fails_closed(self):
        cases = (
            ("MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN", "https://other.example",
             "approved_origin_mismatch", "https://stage.example", "room-116", "m116-operation-0001"),
            ("MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID", "other-room",
             "approved_conversation_mismatch", "https://stage.example", "room-116", "m116-operation-0001"),
            ("MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID", "m116-operation-0002",
             "approved_operation_mismatch", "https://stage.example", "room-116", "m116-operation-0001"),
        )
        for key, value, error, origin, room, operation in cases:
            env = ENV.copy()
            env[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                validate_environment(env, origin, room, operation)

    def test_missing_or_malformed_operation_is_rejected(self):
        env = ENV.copy()
        del env["MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID"]
        with self.assertRaisesRegex(ValueError, "approved_operation_mismatch"):
            validate_environment(env, "https://stage.example", "room-116", "m116-operation-0001")
        with self.assertRaisesRegex(ValueError, "approved_operation_binding_required"):
            validate_environment(ENV.copy(), "https://stage.example", "room-116", "bad")

    def test_missing_execution_or_staging_gate_still_fails(self):
        for key, error in (
            ("MESSENGER_FIRST_CONTACT_EXECUTE", "explicit_execution_gate_required"),
            ("MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED", "explicit_staging_authorization_required"),
        ):
            env = ENV.copy()
            env[key] = "false"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                validate_environment(env, "https://stage.example", "room-116", "m116-operation-0001")


if __name__ == "__main__":
    unittest.main()
