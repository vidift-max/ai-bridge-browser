import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_first_contact_release_readiness import release_readiness


ENV = {
    "MESSENGER_TOKEN_AI_A": "synthetic-release-token-a",
    "MESSENGER_TOKEN_AI_B": "synthetic-release-token-b",
    "MESSENGER_AI_ID_A": "AI-01",
    "MESSENGER_AI_ID_B": "AI-02",
    "MESSENGER_ENVIRONMENT": "staging",
    "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
    "MESSENGER_STORAGE_MODE": "ephemeral",
    "MESSENGER_DB_PATH": ":memory:",
    "MESSENGER_FIRST_CONTACT_OPERATION_ID": "mission120-operation-0001",
}


class Mission120ReleaseReadinessTest(unittest.TestCase):
    def run_gate(self, env=None, room="default", origin="https://stage.example"):
        return release_readiness(ROOT / "render.staging.yaml", origin,
                                  room, (env or ENV).copy())

    def test_complete_readiness_passes_without_authorizing_or_contacting(self):
        result = self.run_gate()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["blueprint"], "valid")
        self.assertEqual(result["conversation"], "default_verified")
        self.assertEqual(result["authorization"], "NOT_GRANTED")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["deployment"], "NOT_PERFORMED")
        self.assertEqual(result["realContact"], "NOT_STARTED")
        self.assertNotIn("synthetic-release-token", str(result))
        self.assertNotIn("stage.example", str(result))
        self.assertNotIn("mission120-operation", str(result))

    def test_only_current_bootstrap_conversation_is_accepted(self):
        result = self.run_gate(room="other-room")
        self.assertEqual(result["result"], "NO_GO")
        self.assertIn("current_bootstrap_requires_default_conversation",
                      result["failures"])
        self.assertEqual(result["network"], "NOT_CONTACTED")

    def test_non_https_origin_fails_closed(self):
        result = self.run_gate(origin="http://stage.example")
        self.assertEqual(result["result"], "NO_GO")
        self.assertEqual(result["authorization"], "NOT_GRANTED")
        self.assertEqual(result["network"], "NOT_CONTACTED")

    def test_missing_credentials_fail_closed_without_echo(self):
        env = ENV.copy()
        env["MESSENGER_TOKEN_AI_A"] = ""
        result = self.run_gate(env=env)
        self.assertEqual(result["result"], "NO_GO")
        self.assertNotIn("synthetic-release-token", str(result))

    def test_duplicate_credentials_fail_closed(self):
        env = ENV.copy()
        env["MESSENGER_TOKEN_AI_B"] = env["MESSENGER_TOKEN_AI_A"]
        result = self.run_gate(env=env)
        self.assertEqual(result["result"], "NO_GO")

    def test_every_execution_and_bound_approval_value_must_remain_unset(self):
        approval_keys = (
            "MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED",
            "MESSENGER_FIRST_CONTACT_EXECUTE",
            "MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN",
            "MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID",
            "MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID",
        )
        for key in approval_keys:
            env = ENV.copy()
            env[key] = "true" if key.endswith(("AUTHORIZED", "EXECUTE")) else "stale-value"
            with self.subTest(key=key):
                result = self.run_gate(env=env)
                self.assertEqual(result["result"], "NO_GO")
                self.assertIn("execution_authorization_must_remain_unset",
                              result["failures"])

    def test_missing_operation_id_fails_closed(self):
        env = ENV.copy()
        del env["MESSENGER_FIRST_CONTACT_OPERATION_ID"]
        result = self.run_gate(env=env)
        self.assertEqual(result["result"], "NO_GO")

    def test_persistent_storage_environment_fails_closed(self):
        env = ENV.copy()
        env["MESSENGER_DB_PATH"] = "/var/data/messages.sqlite"
        result = self.run_gate(env=env)
        self.assertEqual(result["result"], "NO_GO")
        self.assertEqual(result["deployment"], "NOT_PERFORMED")


if __name__ == "__main__":
    unittest.main()
