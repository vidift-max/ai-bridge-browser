import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FirebaseRulesParityTest(unittest.TestCase):
    def test_deployment_rule_files_are_identical(self):
        canonical = json.loads((ROOT / "firebase" / "database.rules.json").read_text(encoding="utf-8"))
        deploy_config = json.loads((ROOT / "config" / "firebase" / "database.rules.json").read_text(encoding="utf-8"))
        self.assertEqual(canonical, deploy_config)

    def test_message_writes_require_authenticated_membership_and_new_record(self):
        rules = json.loads((ROOT / "firebase" / "database.rules.json").read_text(encoding="utf-8"))["rules"]["messenger"]
        message = rules["conversations"]["$conversationId"]["messages"]["$messageId"]
        self.assertIn("auth != null", message[".write"])
        self.assertIn("members", message[".write"])
        self.assertIn("!data.exists()", message[".write"])
        self.assertIn("senderAiId", message[".validate"])

    def test_ack_write_is_bound_to_authenticated_ai_identity_and_membership(self):
        rules = json.loads((ROOT / "firebase" / "database.rules.json").read_text(encoding="utf-8"))["rules"]["messenger"]
        ack = rules["conversations"]["$conversationId"]["acks"]["$messageId"]["$aiId"]
        self.assertIn("auth != null", ack[".write"])
        self.assertIn("identitiesByUid", ack[".write"])
        self.assertIn("members", ack[".write"])
        self.assertEqual(ack[".validate"], "newData.val() === true")


if __name__ == "__main__":
    unittest.main()
