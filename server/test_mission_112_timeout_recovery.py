import unittest
from unittest.mock import Mock, call

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact as runner


class Mission112TimeoutRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "messageId": "first-contact-stable-message",
            "conversationId": "room-1",
            "recipientAiIds": ["AI-02"],
            "body": "first contact",
            "clientRequestId": "first-contact-stable-request",
        }

    def test_transport_timeout_replays_exact_same_idempotent_request_once(self):
        request = Mock(side_effect=[
            (0, {"error": "TimeoutError"}),
            (200, {"state": "QUEUED", "messageId": self.payload["messageId"]}),
        ])
        status, body = runner._submit_with_bounded_recovery(
            request, "https://stage.example", "ai01-token", self.payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["state"], "QUEUED")
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list, [
            call("https://stage.example", "/v1/messages", "ai01-token", "POST", self.payload),
            call("https://stage.example", "/v1/messages", "ai01-token", "POST", self.payload),
        ])

    def test_server_5xx_replays_once_with_same_idempotency_identifiers(self):
        request = Mock(side_effect=[
            (503, {"error": "http_error"}),
            (200, {"state": "QUEUED"}),
        ])
        status, _ = runner._submit_with_bounded_recovery(
            request, "https://stage.example", "ai01-token", self.payload)
        self.assertEqual(status, 200)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[0].args[4], request.call_args_list[1].args[4])

    def test_second_ambiguous_result_stops_without_third_attempt(self):
        request = Mock(return_value=(0, {"error": "TimeoutError"}))
        with self.assertRaisesRegex(RuntimeError, "message_submit_outcome_ambiguous"):
            runner._submit_with_bounded_recovery(
                request, "https://stage.example", "ai01-token", self.payload)
        self.assertEqual(request.call_count, 2)

    def test_client_error_is_not_retried(self):
        request = Mock(return_value=(401, {"error": "http_error"}))
        status, body = runner._submit_with_bounded_recovery(
            request, "https://stage.example", "ai01-token", self.payload)
        self.assertEqual(status, 401)
        self.assertEqual(body, {"error": "http_error"})
        request.assert_called_once()

    def test_success_is_not_retried(self):
        request = Mock(return_value=(200, {"state": "QUEUED"}))
        status, _ = runner._submit_with_bounded_recovery(
            request, "https://stage.example", "ai01-token", self.payload)
        self.assertEqual(status, 200)
        request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
