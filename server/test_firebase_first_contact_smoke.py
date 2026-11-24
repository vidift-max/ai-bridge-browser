import unittest
from unittest.mock import patch

from tools.firebase_first_contact_smoke import ProbeError, validate_config, run_probe, authorize_send


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


    def test_explicit_send_waits_for_recipient_and_verifies_ack(self):
        config = validate_config(BASE)
        message = {
            "senderAiId": "AI-01",
            "recipientAiIds": {"AI-02": True},
            "body": "first-contact-fixednonce",
        }
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
            {"name": "-message-key"},
            {"-message-key": message},
            True,
            True,
        ]
        with patch("tools.firebase_first_contact_smoke.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "fixednonce"
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
                result = run_probe(config, send=True, wait_seconds=1)
        self.assertEqual(result["state"], "TEXT_ROUND_TRIP_PASS")
        self.assertEqual(result["message_round_trip"], "PASS")
        self.assertEqual(result["acknowledgement"], "VERIFIED")
        self.assertEqual(request.call_count, 7)
        self.assertEqual(request.call_args_list[3].args[1], "POST")
        self.assertIn("/acks/-message-key/AI-02", request.call_args_list[5].args[2])


    def test_explicit_loopback_emulator_mode_requires_namespace(self):
        env = dict(BASE, MESSENGER_FIREBASE_DATABASE_URL="http://127.0.0.1:9000/?ns=demo-ai-bridge-rules", MESSENGER_FIREBASE_EMULATOR="true")
        config = validate_config(env)
        self.assertEqual(config["database_url"], "http://127.0.0.1:9000")
        self.assertEqual(config["database_namespace"], "demo-ai-bridge-rules")

    def test_emulator_mode_rejects_non_loopback_and_missing_namespace(self):
        for url in ("http://example.com:9000/?ns=demo", "http://127.0.0.1:9000/", "https://127.0.0.1:9000/?ns=demo"):
            with self.subTest(url=url):
                env = dict(BASE, MESSENGER_FIREBASE_DATABASE_URL=url, MESSENGER_FIREBASE_EMULATOR="true")
                with self.assertRaisesRegex(ProbeError, "invalid_firebase_emulator_url"):
                    validate_config(env)

    def test_emulator_namespace_is_added_to_authenticated_requests(self):
        config = validate_config(dict(BASE, MESSENGER_FIREBASE_DATABASE_URL="http://127.0.0.1:9000/?ns=demo-ai-bridge-rules", MESSENGER_FIREBASE_EMULATOR="true"))
        with patch("tools.firebase_first_contact_smoke.urllib.request.urlopen") as urlopen:
            response = urlopen.return_value.__enter__.return_value
            response.read.return_value = b'{"ok":true}'
            from tools.firebase_first_contact_smoke import firebase_request
            firebase_request(config, "GET", "/messenger/identities/AI-01", "secret-token")
            request = urlopen.call_args.args[0]
            self.assertIn("ns=demo-ai-bridge-rules", request.full_url)
            self.assertIn("auth=secret-token", request.full_url)


    def test_production_send_is_blocked_without_double_opt_in(self):
        config = validate_config(BASE)
        with self.assertRaisesRegex(ProbeError, "production_send_requires_cli_and_environment_opt_in"):
            authorize_send(config, BASE, send=True, allow_production_send=False)
        with self.assertRaisesRegex(ProbeError, "production_send_requires_cli_and_environment_opt_in"):
            authorize_send(config, dict(BASE, MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND="true"),
                           send=True, allow_production_send=False)
        with self.assertRaisesRegex(ProbeError, "production_send_requires_cli_and_environment_opt_in"):
            authorize_send(config, BASE, send=True, allow_production_send=True)

    def test_production_send_requires_both_explicit_opt_ins(self):
        config = validate_config(BASE)
        env = dict(BASE, MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND="true")
        authorize_send(config, env, send=True, allow_production_send=True)

    def test_emulator_send_does_not_require_production_opt_in(self):
        env = dict(BASE, MESSENGER_FIREBASE_DATABASE_URL="http://127.0.0.1:9000/?ns=demo-ai-bridge-rules",
                   MESSENGER_FIREBASE_EMULATOR="true")
        config = validate_config(env)
        authorize_send(config, env, send=True, allow_production_send=False)

    def test_preflight_never_requires_production_send_opt_in(self):
        config = validate_config(BASE)
        authorize_send(config, BASE, send=False, allow_production_send=False)



if __name__ == "__main__":
    unittest.main()

    def test_production_readiness_report_is_sanitized_and_explicitly_non_operational(self):
        from tools.firebase_first_contact_smoke import production_readiness_report
        report = production_readiness_report(validate_config(BASE))
        serialized = __import__("json").dumps(report, sort_keys=True)
        self.assertEqual(report["state"], "CONFIGURATION_VALID")
        self.assertEqual(report["network_check"], "NOT_RUN")
        self.assertEqual(report["identity_provisioning"], "NOT_VERIFIED")
        self.assertEqual(report["conversation_membership"], "NOT_VERIFIED")
        self.assertEqual(report["message_send"], "NOT_RUN")
        self.assertNotIn("token-a-secret", serialized)
        self.assertNotIn("token-b-secret", serialized)

    def test_production_url_rejects_custom_port_and_nested_path(self):
        for url in ("https://demo-default-rtdb.firebaseio.com:8443",
                    "https://demo-default-rtdb.firebaseio.com/nested/path"):
            with self.subTest(url=url):
                env = dict(BASE, MESSENGER_FIREBASE_DATABASE_URL=url)
                with self.assertRaisesRegex(ProbeError, "invalid_firebase_database_url"):
                    validate_config(env)

    def test_production_readiness_configuration_does_not_make_network_requests(self):
        from tools.firebase_first_contact_smoke import production_readiness_report
        with patch("tools.firebase_first_contact_smoke.firebase_request") as request:
            report = production_readiness_report(validate_config(BASE))
        request.assert_not_called()
        self.assertEqual(report["message_send"], "NOT_RUN")
