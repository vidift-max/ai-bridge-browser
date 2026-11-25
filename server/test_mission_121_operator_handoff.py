import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_first_contact_operator_handoff import build_handoff


class Mission121OperatorHandoffTest(unittest.TestCase):
    def test_valid_blueprint_produces_ordered_incomplete_handoff(self):
        result = build_handoff(ROOT / "render.staging.yaml")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["authorization"], "NOT_GRANTED")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["deployment"], "NOT_PERFORMED")
        self.assertEqual(result["realContact"], "NOT_STARTED")
        self.assertEqual(result["constraints"]["conversationId"], "default")
        self.assertEqual([s["id"] for s in result["steps"]], [
            "create_free_staging", "configure_private_credentials", "manual_deploy",
            "health_readiness", "offline_release_preflight", "explicit_user_approval",
            "first_contact_and_ack",
        ])
        self.assertTrue(all(step["complete"] is False for step in result["steps"]))

    def test_approval_precedes_first_contact(self):
        result = build_handoff(ROOT / "render.staging.yaml")
        ids = [step["id"] for step in result["steps"]]
        self.assertLess(ids.index("explicit_user_approval"), ids.index("first_contact_and_ack"))
        self.assertEqual(result["steps"][-1]["requires"],
                         "explicit_user_approval_and_operator_action")

    def test_handoff_never_contains_secret_values_or_fake_origin(self):
        result = build_handoff(ROOT / "render.staging.yaml")
        serialized = str(result)
        for secret in ("MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B", "Bearer ",
                       "stage.example", "operation-id-value"):
            self.assertNotIn(secret, serialized)

    def test_blueprint_missing_free_plan_fails_closed(self):
        source = (ROOT / "render.staging.yaml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "render.yaml"
            path.write_text(source.replace("plan: free", "plan: starter"), encoding="utf-8")
            result = build_handoff(path)
        self.assertEqual(result["result"], "NO_GO")
        self.assertIn("free_plan", result["failures"])
        self.assertEqual(result["steps"], [])

    def test_blueprint_persistent_disk_fails_closed(self):
        source = (ROOT / "render.staging.yaml").read_text(encoding="utf-8") + "\n  - type: disk\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "render.yaml"
            path.write_text(source, encoding="utf-8")
            result = build_handoff(path)
        self.assertEqual(result["result"], "NO_GO")
        self.assertIn("persistent_disk_absent", result["failures"])

    def test_unreadable_blueprint_returns_redacted_no_go(self):
        result = build_handoff(ROOT / "does-not-exist-mission-121.yaml")
        self.assertEqual(result["result"], "NO_GO")
        self.assertEqual(result["failures"], ["blueprint_unreadable"])
        self.assertEqual(result["network"], "NOT_CONTACTED")

    def test_handoff_declares_free_manual_ephemeral_long_poll_contract(self):
        result = build_handoff(ROOT / "render.staging.yaml")
        self.assertEqual(result["constraints"], {
            "plan": "free", "region": "oregon", "deploy": "manual_only",
            "storage": "ephemeral_in_memory", "persistentDisk": False,
            "transport": "HTTP_LONG_POLL", "conversationId": "default",
        })


if __name__ == "__main__":
    unittest.main()
