import unittest
from unittest.mock import patch

from tools.firebase_first_contact_smoke import ProbeError, validate_config, run_probe


BASE = {
    "MESSENGER_FIREBASE_DATABASE_URL": "https://demo-default-rtdb.firebaseio.com/",
    "MESSENGER_FIREBASE_AI_A_ID": "AI-01",
    "MESSENGER_FIREBASE_AI_B_ID": "AI-02",
    "MESSENGER_FIREBASE_AI_A_ID_TOKEN": "token-a-secret",
    "MESSENGER_FIREBASE_AI_B_ID_TOKEN": "token-b-secret",
    "MESSENGER_FIREBASE_CONVERSATION_ID": "private-ai-01-ai-02",
}


class FirebaseFirstContactSmokeTest(unittest.TestCase):
    def test_validates_distinct_identity_pair_without_printing_tokens(self):
        config = validate_config(BASE)
        self.assertEqual(config["ai_a"], "AI-01")
        self.assertEqual(config["ai_b"], "AI-02")
        self.assertEqual(config["database_url"], "https://demo-default-rtdb.firebaseio.com")

    def test_fails_closed_when_token_missing(self):
        env = dict(BASE)
        del env["MESSENGER_FIREBASE_AI_B_ID_TOKEN"]
        with self.assertRaisesRegex(ProbeError, "missing_configuration"):
            validate_config(env)

    def test_rejects_same_ai_identity(self):
        env = dict(BASE, MESSENGER_FIREBASE_AI_B_ID="AI-01")
        with self.assertRaisesRegex(ProbeError, "identities_must_be_distinct"):
            validate_config(env)

    def test_rejects_non_firebase_or_non_https_database(self):
        for url in ("http://demo.firebaseio.com", "https://example.com", "https://demo.firebaseio.com?x=1"):
            with self.subTest(url=url):
                env = dict(BASE, MESSENGER_FIREBASE_DATABASE_URL=url)
                with self.assertRaisesRegex(ProbeError, "invalid_firebase_database_url"):
                    validate_config(env)

    def test_preflight_requires_both_identity_mappings_and_room_membership(self):
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            with self.assertRaisesRegex(ProbeError, "conversation_membership_not_ready"):
                run_probe(config)

    def test_preflight_pass_does_not_send_message(self):
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
            result = run_probe(config, send=False)
        self.assertEqual(result["state"], "PREFLIGHT_PASS")
        self.assertEqual(result["message_round_trip"], "NOT_RUN")
        self.assertEqual(request.call_count, 3)


if __name__ == "__main__":
    unittest.main()
