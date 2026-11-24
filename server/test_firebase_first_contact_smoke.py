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

    def test_config_check_cli_validates_without_network_or_secret_output(self):
        import contextlib
        import io
        import json
        from unittest.mock import patch
        from tools.firebase_first_contact_smoke import main
        output = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with patch("tools.firebase_first_contact_smoke.firebase_request") as request:
                with contextlib.redirect_stdout(output):
                    exit_code = main(["--config-check"])
        request.assert_not_called()
        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["state"], "CONFIGURATION_VALID")
        self.assertNotIn("token-a-secret", output.getvalue())
        self.assertNotIn("token-b-secret", output.getvalue())

    def test_config_check_cli_rejects_send_flags(self):
        import contextlib
        import io
        from tools.firebase_first_contact_smoke import main
        errors = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with contextlib.redirect_stderr(errors):
                exit_code = main(["--config-check", "--send"])
        self.assertEqual(exit_code, 2)
        self.assertIn("config_check_cannot_be_combined", errors.getvalue())


    def test_readonly_preflight_reports_both_identity_mappings_and_memberships(self):
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
            result = run_probe(config, send=False)
        self.assertEqual(result["identity_mappings"], {"AI-01": "VERIFIED", "AI-02": "VERIFIED"})
        self.assertEqual(result["conversation_membership"], {
            "AI-01": "VERIFIED_MEMBER", "AI-02": "VERIFIED_MEMBER"})
        self.assertEqual(result["write_operations"], "NONE")
        self.assertEqual(result["message_round_trip"], "NOT_RUN")
        self.assertEqual([call.args[1] for call in request.call_args_list], ["GET", "GET", "GET"])

    def test_preflight_rejects_identity_mapping_for_wrong_ai_id(self):
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-99", "uid": "uid-a"},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            with self.assertRaisesRegex(ProbeError, "ai_a_identity_not_provisioned"):
                run_probe(config, send=False)

    def test_preflight_rejects_shared_firebase_uid(self):
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "same-uid"},
            {"aiId": "AI-02", "uid": "same-uid"},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            with self.assertRaisesRegex(ProbeError, "firebase_uids_not_distinct"):
                run_probe(config, send=False)

    def test_preflight_cli_outputs_verified_read_only_state(self):
        import contextlib
        import io
        import json
        from tools.firebase_first_contact_smoke import main
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        output = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
                with contextlib.redirect_stdout(output):
                    exit_code = main(["--preflight"])
        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["state"], "PREFLIGHT_PASS")
        self.assertEqual(result["write_operations"], "NONE")
        self.assertEqual(request.call_count, 3)
        self.assertTrue(all(call.args[1] == "GET" for call in request.call_args_list))
        self.assertNotIn("token-a-secret", output.getvalue())
        self.assertNotIn("token-b-secret", output.getvalue())

    def test_preflight_cli_rejects_send_options(self):
        import contextlib
        import io
        from tools.firebase_first_contact_smoke import main
        errors = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with contextlib.redirect_stderr(errors):
                exit_code = main(["--preflight", "--send"])
        self.assertEqual(exit_code, 2)
        self.assertIn("preflight_cannot_be_combined_with_send_options", errors.getvalue())



    def test_prepare_send_plan_is_read_only_and_contains_no_credentials(self):
        import json
        from tools.firebase_first_contact_smoke import prepare_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "dryrunnonce"
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
                plan = prepare_send_plan(config)
        serialized = json.dumps(plan, sort_keys=True)
        self.assertEqual(plan["state"], "SEND_PLAN_READY")
        self.assertEqual(plan["preflight"], "PREFLIGHT_PASS")
        self.assertEqual(plan["sender"], "AI-01")
        self.assertEqual(plan["recipient"], "AI-02")
        self.assertEqual(plan["payload"]["recipientAiIds"], {"AI-02": True})
        self.assertEqual(plan["write_operations"], "NONE")
        self.assertEqual(plan["send_operation"], "NOT_EXECUTED")
        self.assertEqual(plan["acknowledgement"], "NOT_RUN")
        self.assertEqual(request.call_count, 3)
        self.assertTrue(all(call.args[1] == "GET" for call in request.call_args_list))
        self.assertNotIn("token-a-secret", serialized)
        self.assertNotIn("token-b-secret", serialized)

    def test_prepare_send_cli_emits_plan_without_any_write_operation(self):
        import contextlib
        import io
        import json
        from tools.firebase_first_contact_smoke import main
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        output = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
                with contextlib.redirect_stdout(output):
                    exit_code = main(["--prepare-send"])
        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["state"], "SEND_PLAN_READY")
        self.assertEqual(result["send_operation"], "NOT_EXECUTED")
        self.assertEqual(request.call_count, 3)
        self.assertTrue(all(call.args[1] == "GET" for call in request.call_args_list))
        self.assertNotIn("token-a-secret", output.getvalue())
        self.assertNotIn("token-b-secret", output.getvalue())

    def test_prepare_send_cli_rejects_send_and_production_opt_in_flags(self):
        import contextlib
        import io
        from tools.firebase_first_contact_smoke import main
        for args in (["--prepare-send", "--send"],
                     ["--prepare-send", "--allow-production-send"]):
            errors = io.StringIO()
            with patch.dict("os.environ", BASE, clear=True):
                with contextlib.redirect_stderr(errors):
                    exit_code = main(args)
            self.assertEqual(exit_code, 2)
            self.assertIn("prepare_send_cannot_be_combined_with_send_options", errors.getvalue())


    def test_send_plan_contains_payload_digest_and_validates_pair_binding(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(len(plan["plan_sha256"]), 64)
        self.assertEqual(len(plan["payload_sha256"]), 64)
        self.assertTrue(validate_send_plan(plan, config))
        other_pair = dict(config, ai_b="AI-03")
        with self.assertRaisesRegex(ProbeError, "send_plan_identity_binding_invalid"):
            validate_send_plan(plan, other_pair)

    def test_send_plan_detects_payload_tampering(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        plan["payload"]["body"] = "altered after planning"
        with self.assertRaisesRegex(ProbeError, "send_plan_payload_integrity_mismatch"):
            validate_send_plan(plan, config)

    def test_send_plan_rejects_extra_recipient_and_oversized_body(self):
        from tools.firebase_first_contact_smoke import validate_send_plan, _canonical_payload_bytes
        import hashlib
        config = validate_config(BASE)
        plan = {
            "schema_version": 2, "state": "SEND_PLAN_READY", "preflight": "PREFLIGHT_PASS",
            "sender": "AI-01", "recipient": "AI-02",
            "conversation_id": "private-ai-01-ai-02", "operation": "ONE_TEXT_MESSAGE",
            "payload": {"senderAiId": "AI-01", "recipientAiIds": {"AI-02": True, "AI-03": True},
                        "body": "x" * 281, "messageKind": "NORMAL", "createdAtEpochMs": 1},
            "write_operations": "NONE", "send_operation": "NOT_EXECUTED",
            "acknowledgement": "NOT_RUN", "credentials_included": False,
        }
        plan["payload_sha256"] = hashlib.sha256(_canonical_payload_bytes(plan["payload"])).hexdigest()
        with self.assertRaisesRegex(ProbeError, "send_plan_recipient_or_kind_invalid"):
            validate_send_plan(plan, config)

    def test_send_plan_rejects_modified_safety_metadata(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        plan["send_operation"] = "EXECUTED"
        with self.assertRaisesRegex(ProbeError, "send_plan_safety_metadata_invalid"):
            validate_send_plan(plan, config)


    def test_send_plan_rejects_oversized_body_even_with_matching_digest(self):
        from tools.firebase_first_contact_smoke import validate_send_plan, _canonical_payload_bytes
        import hashlib
        config = validate_config(BASE)
        payload = {"senderAiId": "AI-01", "recipientAiIds": {"AI-02": True},
                   "body": "x" * 281, "messageKind": "NORMAL", "createdAtEpochMs": 1}
        plan = {"schema_version": 2, "state": "SEND_PLAN_READY", "preflight": "PREFLIGHT_PASS",
                "operation": "ONE_TEXT_MESSAGE", "sender": "AI-01",
                "recipient": "AI-02", "conversation_id": "private-ai-01-ai-02",
                "payload": payload, "payload_sha256": hashlib.sha256(_canonical_payload_bytes(payload)).hexdigest(),
                "write_operations": "NONE", "send_operation": "NOT_EXECUTED",
                "acknowledgement": "NOT_RUN", "credentials_included": False}
        with self.assertRaisesRegex(ProbeError, "send_plan_body_invalid"):
            validate_send_plan(plan, config)


    def test_plan_file_is_created_private_and_never_overwritten(self):
        import os
        import tempfile
        from tools.firebase_first_contact_smoke import prepare_send_plan, save_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "plan.json")
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
                plan = prepare_send_plan(config)
            save_send_plan(plan, path)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(ProbeError, "send_plan_file_already_exists"):
                save_send_plan(plan, path)

    def test_plan_file_round_trip_verifies_locally_without_firebase(self):
        import os
        import tempfile
        from tools.firebase_first_contact_smoke import prepare_send_plan, save_send_plan, load_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "plan.json")
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies) as request:
                plan = prepare_send_plan(config)
                save_send_plan(plan, path)
                loaded = load_send_plan(path)
                self.assertTrue(validate_send_plan(loaded, config))
            self.assertEqual(request.call_count, 3)

    def test_plan_file_rejects_symlink(self):
        import os
        import tempfile
        from tools.firebase_first_contact_smoke import load_send_plan
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "target.json")
            link = os.path.join(directory, "link.json")
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("{}")
            os.symlink(target, link)
            with self.assertRaisesRegex(ProbeError, "send_plan_file_open_failed"):
                load_send_plan(link)

    def test_verify_plan_cli_is_local_and_redacts_credentials(self):
        import contextlib
        import io
        import json
        import os
        import tempfile
        from tools.firebase_first_contact_smoke import prepare_send_plan, save_send_plan, main
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "plan.json")
            with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
                plan = prepare_send_plan(config)
            save_send_plan(plan, path)
            output = io.StringIO()
            with patch.dict("os.environ", BASE, clear=True):
                with patch("tools.firebase_first_contact_smoke.firebase_request") as request:
                    with contextlib.redirect_stdout(output):
                        code = main(["--verify-plan-file", path])
            request.assert_not_called()
            result = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(result["state"], "SEND_PLAN_VALID")
            self.assertEqual(result["firebase_requests"], "NONE")
            self.assertEqual(result["plan_sha256"], plan["plan_sha256"])
            self.assertEqual(result["expires_at_epoch_ms"], plan["expires_at_epoch_ms"])
            self.assertNotIn("token-a-secret", output.getvalue())
            self.assertNotIn("token-b-secret", output.getvalue())

    def test_plan_output_requires_prepare_send(self):
        import contextlib
        import io
        from tools.firebase_first_contact_smoke import main
        errors = io.StringIO()
        with patch.dict("os.environ", BASE, clear=True):
            with contextlib.redirect_stderr(errors):
                code = main(["--plan-output", "plan.json"])
        self.assertEqual(code, 2)
        self.assertIn("plan_output_requires_prepare_send", errors.getvalue())


    def test_send_plan_is_valid_at_expiry_boundary_and_rejected_after(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        self.assertTrue(validate_send_plan(plan, config, now_ms=plan["expires_at_epoch_ms"]))
        with self.assertRaisesRegex(ProbeError, "send_plan_expired"):
            validate_send_plan(plan, config, now_ms=plan["expires_at_epoch_ms"] + 1)

    def test_send_plan_rejects_future_creation_timestamp(self):
        import hashlib
        import time
        from tools.firebase_first_contact_smoke import (
            prepare_send_plan, validate_send_plan, _canonical_payload_bytes,
            _canonical_plan_bytes, PLAN_TTL_MS,
        )
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        future = int(time.time() * 1000) + 60_000
        plan["created_at_epoch_ms"] = future
        plan["expires_at_epoch_ms"] = future + PLAN_TTL_MS
        plan["payload"]["createdAtEpochMs"] = future
        plan["payload_sha256"] = hashlib.sha256(_canonical_payload_bytes(plan["payload"])).hexdigest()
        plan["plan_sha256"] = hashlib.sha256(_canonical_plan_bytes(plan)).hexdigest()
        with self.assertRaisesRegex(ProbeError, "send_plan_timestamp_in_future"):
            validate_send_plan(plan, config, now_ms=future - 30_001)

    def test_send_plan_expiry_is_bound_to_creation_time(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        plan["expires_at_epoch_ms"] += 1
        with self.assertRaisesRegex(ProbeError, "send_plan_expiry_invalid"):
            validate_send_plan(plan, config)

    def test_send_plan_full_envelope_metadata_is_integrity_protected(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        plan["preflight"] = "SKIPPED"
        with self.assertRaisesRegex(ProbeError, "send_plan_identity_binding_invalid"):
            validate_send_plan(plan, config)

    def test_send_plan_rejects_boolean_timestamps(self):
        from tools.firebase_first_contact_smoke import prepare_send_plan, validate_send_plan
        config = validate_config(BASE)
        replies = [
            {"aiId": "AI-01", "uid": "uid-a"},
            {"aiId": "AI-02", "uid": "uid-b"},
            {"members": {"AI-01": True, "AI-02": True}},
        ]
        with patch("tools.firebase_first_contact_smoke.firebase_request", side_effect=replies):
            plan = prepare_send_plan(config)
        plan["created_at_epoch_ms"] = True
        with self.assertRaisesRegex(ProbeError, "send_plan_timestamp_invalid"):
            validate_send_plan(plan, config)


if __name__ == "__main__":
    unittest.main()
