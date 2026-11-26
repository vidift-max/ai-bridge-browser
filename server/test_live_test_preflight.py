import json
import unittest

from server.live_test_preflight import build_preflight, parse_assignment_map


class LiveTestPreflightTest(unittest.TestCase):
    def env(self, **values):
        base = {
            "MESSENGER_AI_PROVIDER_MAP": json.dumps({"AI-USER": "openai", "AI-PEER": "anthropic"}),
            "OPENAI_API_KEY": "openai-secret",
            "ANTHROPIC_API_KEY": "anthropic-secret",
            "OPENAI_API_CALLS_ENABLED": "true",
            "ANTHROPIC_API_CALLS_ENABLED": "true",
            "AI_PROVIDER_HOST_HMAC_KEY_HEX": "aa" * 32,
        }
        base.update(values)
        return base

    def test_complete_preflight_is_ready_without_network(self):
        result = build_preflight(self.env())
        self.assertEqual(result["state"], "READY_FOR_OPERATOR_ACTIVATION")
        self.assertFalse(result["networkCallsPerformed"])
        self.assertFalse(result["secretsExposed"])
        self.assertTrue(all(item["ok"] for item in result["checks"]))
        encoded = json.dumps(result)
        self.assertNotIn("openai-secret", encoded)
        self.assertNotIn("anthropic-secret", encoded)

    def test_missing_key_is_blocked(self):
        result = build_preflight(self.env(ANTHROPIC_API_KEY=""))
        self.assertEqual(result["state"], "BLOCKED")
        check = next(x for x in result["checks"] if x["id"] == "credential:AI-PEER")
        self.assertFalse(check["ok"])

    def test_disabled_policy_is_blocked(self):
        result = build_preflight(self.env(ANTHROPIC_API_CALLS_ENABLED="false"))
        self.assertEqual(result["state"], "BLOCKED")
        check = next(x for x in result["checks"] if x["id"] == "policy:AI-PEER")
        self.assertFalse(check["ok"])

    def test_missing_assignment_is_blocked(self):
        result = build_preflight(self.env(
            MESSENGER_AI_PROVIDER_MAP=json.dumps({"AI-USER": "openai"})))
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("missing", next(
            x for x in result["checks"] if x["id"] == "two_ai_assignments")["detail"])

    def test_invalid_and_duplicate_assignments_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid_provider_assignment"):
            parse_assignment_map("[]")
        with self.assertRaisesRegex(ValueError, "invalid_provider_assignment"):
            parse_assignment_map('{"AI-A":"unknown"}')
        with self.assertRaisesRegex(ValueError, "duplicate_provider_assignment"):
            parse_assignment_map('{"AI-A":"openai","AI-A":"anthropic"}')

    def test_invalid_host_key_is_blocked(self):
        result = build_preflight(self.env(AI_PROVIDER_HOST_HMAC_KEY_HEX="00"))
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(next(x for x in result["checks"] if x["id"] == "host_hmac_key")["ok"])



    def test_same_provider_for_both_ai_ids_is_blocked(self):
        result = build_preflight(self.env(
            MESSENGER_AI_PROVIDER_MAP=json.dumps({
                "AI-USER": "openai", "AI-PEER": "openai"})))
        self.assertEqual(result["state"], "BLOCKED")
        check = next(x for x in result["checks"] if x["id"] == "independent_providers")
        self.assertFalse(check["ok"])

    def test_extra_provider_assignment_is_blocked_for_first_two_ai_test(self):
        result = build_preflight(self.env(
            MESSENGER_AI_PROVIDER_MAP=json.dumps({
                "AI-USER": "openai", "AI-PEER": "anthropic", "AI-EXTRA": "google_gemini"})))
        self.assertEqual(result["state"], "BLOCKED")
        check = next(x for x in result["checks"] if x["id"] == "two_ai_assignments")
        self.assertFalse(check["ok"])

if __name__ == "__main__":
    unittest.main()
