import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "firebase" / "database.rules.json"


class FirebaseRulesContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))["rules"]["messenger"]

    def test_group_creation_and_join_are_bounded_to_twenty(self):
        conversations = self.rules["conversations"]["$conversationId"]
        self.assertIn("<= 20", conversations[".validate"])
        self.assertIn("newData.child('memberCount').val() <= 20", conversations[".write"])
        self.assertIn("newData.child('memberCount').val() + 1", conversations[".write"])

    def test_invite_claim_is_required_for_join(self):
        join_rule = self.rules["conversations"]["$conversationId"][".write"]
        self.assertIn("invitesByAi", join_rule)
        self.assertIn("!data.child('members').child", join_rule)

    def test_invite_claim_is_authenticated_and_expiring(self):
        claim_rule = self.rules["invitesByAi"]["$aiId"]["$conversationId"]["$token"][".write"]
        self.assertIn("auth != null", claim_rule)
        self.assertIn("expiresAtEpochMs", claim_rule)


if __name__ == "__main__":
    unittest.main()
