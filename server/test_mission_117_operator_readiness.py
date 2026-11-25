import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_staging_operator_readiness import audit_blueprint, audit_environment, audit


BLUEPRINT = ROOT / "render.staging.yaml"
ENV = {
    "MESSENGER_TOKEN_AI_A": "synthetic-token-a",
    "MESSENGER_TOKEN_AI_B": "synthetic-token-b",
    "MESSENGER_AI_ID_A": "AI-01",
    "MESSENGER_AI_ID_B": "AI-02",
    "MESSENGER_ENVIRONMENT": "staging",
    "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
    "MESSENGER_STORAGE_MODE": "ephemeral",
    "MESSENGER_DB_PATH": ":memory:",
}


class Mission117OperatorReadinessTest(unittest.TestCase):
    def test_repository_blueprint_passes_static_safety_audit(self):
        self.assertEqual(audit_blueprint(BLUEPRINT.read_text(encoding="utf-8")), [])

    def test_each_secret_requires_its_own_sync_false(self):
        source = BLUEPRINT.read_text(encoding="utf-8")
        source = source.replace(
            "- key: MESSENGER_TOKEN_AI_A\n        sync: false",
            "- key: MESSENGER_TOKEN_AI_A\n        sync: true",
        )
        failures = audit_blueprint(source)
        self.assertIn("messenger_token_ai_a_manual_secret", failures)
        self.assertNotIn("messenger_token_ai_b_manual_secret", failures)

    def test_blueprint_rejects_paid_plan_persistent_disk_and_auto_deploy(self):
        source = BLUEPRINT.read_text(encoding="utf-8")
        for changed, expected in (
            (source.replace("plan: free", "plan: starter"), "free_plan"),
            (source.replace("autoDeployTrigger: off", "autoDeployTrigger: commit"), "manual_deploy"),
            (source + "\n  - type: disk\n", "persistent_disk_absent"),
            (source + "\n        mountPath: /var/data\n", "persistent_mount_absent"),
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, audit_blueprint(changed))

    def test_complete_operator_environment_passes_but_never_authorizes(self):
        result = audit(BLUEPRINT, ENV.copy())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["authorization"], "NOT_GRANTED")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["deployment"], "NOT_PERFORMED")
        self.assertEqual(result["realContact"], "NOT_STARTED")
        self.assertNotIn("synthetic-token", str(result))

    def test_missing_or_wrong_environment_fails_closed(self):
        for key, value in (
            ("MESSENGER_TOKEN_AI_A", ""),
            ("MESSENGER_AI_ID_B", "AI-01"),
            ("MESSENGER_ENVIRONMENT", "production"),
            ("MESSENGER_ALLOW_EPHEMERAL_STAGING", "false"),
            ("MESSENGER_STORAGE_MODE", "persistent"),
            ("MESSENGER_DB_PATH", "/var/data/db.sqlite"),
        ):
            env = ENV.copy()
            env[key] = value
            with self.subTest(key=key):
                self.assertTrue(audit_environment(env))

    def test_duplicate_credentials_and_authorization_flags_fail_closed(self):
        env = ENV.copy()
        env["MESSENGER_TOKEN_AI_B"] = env["MESSENGER_TOKEN_AI_A"]
        self.assertIn("credentials_must_be_distinct", audit_environment(env))
        env = ENV.copy()
        env["MESSENGER_FIRST_CONTACT_EXECUTE"] = "true"
        self.assertIn("execution_authorization_must_remain_unset", audit_environment(env))

if __name__ == "__main__":
    unittest.main()
