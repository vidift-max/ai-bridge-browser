import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact as runner


class Mission101FirstContactRunnerTest(unittest.TestCase):
    def test_rejects_same_or_missing_credentials_before_network(self):
        request = Mock()
        for a, b in (("", "b"), ("a", ""), ("same", "same")):
            with self.subTest(a=a, b=b), self.assertRaisesRegex(
                    ValueError, "distinct_ai_credentials_required"):
                runner.run_first_contact("https://stage.example", "room", a, b, request)
        request.assert_not_called()

    def test_rejects_wrong_ai_identity_before_sending(self):
        request = Mock(return_value=(200, {"identity": {"aiId": "AI-03"}}))
        with self.assertRaisesRegex(RuntimeError, "identity_ai_01_mismatch"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", request)
        self.assertEqual(request.call_count, 2)
        self.assertTrue(all(call.args[1] == "/v1/me/identity" for call in request.call_args_list))

    def test_full_first_contact_requires_receive_ack_and_pending_removal(self):
        import threading
        delivered = threading.Event()
        message_id = {"value": None}

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                self.assertEqual(token, "b")
                self.assertTrue(delivered.wait(2))
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": message_id["value"], "conversationId": "room",
                    "senderAiId": "AI-01", "body": "AI-01 -> AI-02 first-contact verification",
                    "sequence": 150}]}
            if path == "/v1/messages":
                self.assertEqual(token, "a")
                self.assertNotIn("senderAiId", payload)
                message_id["value"] = payload["messageId"]
                delivered.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            if path.endswith("/ack"):
                self.assertEqual(token, "b")
                return 200, {"messageId": message_id["value"], "state": "ACKNOWLEDGED", "principalAiId": "AI-02"}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=0" in path:
                self.assertEqual(token, "b")
                self.assertIn("after=149", path)
                self.assertIn("limit=100", path)
                self.assertIn("timeout=0", path)
                return 200, {"principalAiId": "AI-02", "messages": []}
            self.fail("unexpected_request:" + path)

        result = runner.run_first_contact(
            "https://stage.example", "room", "a", "b", fake_request)
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["received"])
        self.assertTrue(result["acknowledged"])
        self.assertTrue(result["removedFromPending"])

    def test_rejects_wrong_recipient_session(self):
        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                return 200, {"principalAiId": "AI-03", "messages": []}
            if path == "/v1/messages":
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "message_received_by_wrong_principal"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)

    def test_rejects_message_that_does_not_match_sender_room_or_body(self):
        import threading
        ready = threading.Event()

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                ready.wait(1)
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": "wrong", "conversationId": "room",
                    "senderAiId": "AI-01", "body": "tampered", "sequence": 1}]}
            if path == "/v1/messages":
                message_id["value"] = payload["messageId"]
                ready.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "message_not_received_exactly_once"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)

    def test_rejects_ack_if_message_remains_pending(self):
        import threading
        ready = threading.Event()
        mid = {"value": None}

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                ready.wait(1)
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": mid["value"], "conversationId": "room",
                    "senderAiId": "AI-01", "body": "AI-01 -> AI-02 first-contact verification",
                    "sequence": 1}]}
            if path == "/v1/messages":
                mid["value"] = payload["messageId"]
                ready.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            if path.endswith("/ack"):
                return 200, {"messageId": mid["value"], "state": "ACKNOWLEDGED", "principalAiId": "AI-02"}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=0" in path:
                return 200, {"principalAiId": "AI-02", "messages": [{"messageId": mid["value"]}]}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "acknowledged_message_still_pending"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)


    def test_rejects_missing_or_invalid_received_sequence_before_ack(self):
        import threading
        ready = threading.Event()
        message_id = {"value": None}

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                ready.wait(1)
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": message_id["value"], "conversationId": "room",
                    "senderAiId": "AI-01", "body": "AI-01 -> AI-02 first-contact verification",
                    "sequence": True}]}
            if path == "/v1/messages":
                ready.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "received_message_sequence_invalid"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)

    def test_response_decoder_never_echoes_untrusted_body(self):
        self.assertEqual(runner._decode(b"secret-token\xff"), {
            "error": "invalid_json_response"})



    def test_rejects_ack_for_different_message_id(self):
        import threading
        ready = threading.Event()
        mid = {"value": None}

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                ready.wait(1)
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": mid["value"], "conversationId": "room",
                    "senderAiId": "AI-01", "body": "AI-01 -> AI-02 first-contact verification",
                    "sequence": 1}]}
            if path == "/v1/messages":
                mid["value"] = payload["messageId"]
                ready.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            if path.endswith("/ack"):
                return 200, {"messageId": "another-message", "state": "ACKNOWLEDGED",
                             "principalAiId": "AI-02"}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "ack_contract_mismatch"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)

    def test_rejects_pending_check_for_wrong_principal(self):
        import threading
        ready = threading.Event()
        mid = {"value": None}

        def fake_request(base, path, token, method="GET", payload=None):
            if path == "/v1/me/identity":
                return 200, {"identity": {"aiId": "AI-01" if token == "a" else "AI-02"}}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=25" in path:
                ready.wait(1)
                return 200, {"principalAiId": "AI-02", "messages": [{
                    "messageId": mid["value"], "conversationId": "room",
                    "senderAiId": "AI-01", "body": "AI-01 -> AI-02 first-contact verification",
                    "sequence": 1}]}
            if path == "/v1/messages":
                mid["value"] = payload["messageId"]
                ready.set()
                return 200, {"state": "QUEUED", "senderAiId": "AI-01"}
            if path.endswith("/ack"):
                return 200, {"messageId": mid["value"], "state": "ACKNOWLEDGED",
                             "principalAiId": "AI-02"}
            if path.startswith("/v1/conversations/room/messages/wait?") and "timeout=0" in path:
                self.assertIn("after=0", path)
                return 200, {"principalAiId": "AI-03", "messages": []}
            self.fail("unexpected_request:" + path)

        with self.assertRaisesRegex(RuntimeError, "pending_check_wrong_principal"):
            runner.run_first_contact("https://stage.example", "room", "a", "b", fake_request)

if __name__ == "__main__":
    unittest.main()
