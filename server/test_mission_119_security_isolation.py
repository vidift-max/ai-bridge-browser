import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.rate_limit import SlidingWindowRateLimiter


class Mission119SecurityIsolationTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {
            "synthetic-ai01-token": "AI-01",
            "synthetic-ai02-token": "AI-02",
            "synthetic-ai03-token": "AI-03",
        }
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens,
            {
                "default": {"AI-01", "AI-02"},
                "private-ai01-ai03": {"AI-01", "AI-03"},
            },
            self.store,
            authenticator=self.auth,
        )
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None

    def request(self, method, path, token=None, payload=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def submit(self, message_id="m119-1", room="default", recipients=None,
               body="security boundary", request_id="m119-request-1", kind="NORMAL"):
        return self.backend.submit(
            "synthetic-ai01-token", message_id, room,
            recipients or ["AI-02"], body, request_id, kind)

    def test_credentials_resolve_to_distinct_authenticated_identities(self):
        self.assertEqual(self.backend.authenticate("synthetic-ai01-token"), "AI-01")
        self.assertEqual(self.backend.authenticate("synthetic-ai02-token"), "AI-02")
        with self.assertRaises(PermissionError):
            self.backend.authenticate("not-a-real-token")

    def test_http_sender_spoof_is_rejected_and_never_persisted(self):
        payload = {
            "messageId": "m119-spoof", "conversationId": "default",
            "recipientAiIds": ["AI-02"], "body": "spoof attempt",
            "clientRequestId": "m119-spoof-request", "senderAiId": "AI-02",
        }
        status, body = self.request("POST", "/v1/messages",
                                    "synthetic-ai01-token", payload)
        self.assertEqual(status, 403)
        self.assertNotIn("synthetic-ai01-token", str(body))
        self.assertEqual(self.backend.pending(
            "synthetic-ai02-token", "default", 0, 10), [])

    def test_sender_identity_is_derived_from_bearer_when_claim_is_omitted(self):
        payload = {
            "messageId": "m119-auth-sender", "conversationId": "default",
            "recipientAiIds": ["AI-02"], "body": "authenticated sender",
            "clientRequestId": "m119-auth-sender-request",
        }
        status, body = self.request("POST", "/v1/messages",
                                    "synthetic-ai01-token", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["senderAiId"], "AI-01")

    def test_nonmember_cannot_read_private_conversation_or_transport_policy(self):
        with self.assertRaises(PermissionError):
            self.backend.pending("synthetic-ai02-token", "private-ai01-ai03", 0, 10)
        with self.assertRaises(PermissionError):
            self.backend.history("synthetic-ai02-token", "private-ai01-ai03", 0, 10)
        with self.assertRaises(PermissionError):
            self.backend.transport_capabilities(
                "synthetic-ai02-token", "private-ai01-ai03")

    def test_pending_is_scoped_to_explicit_recipients_not_all_room_members(self):
        self.submit()
        self.assertEqual(self.backend.pending(
            "synthetic-ai01-token", "default", 0, 10), [])
        received = self.backend.pending(
            "synthetic-ai02-token", "default", 0, 10)
        self.assertEqual([item.message_id for item in received], ["m119-1"])

    def test_only_message_recipient_can_acknowledge(self):
        self.submit(message_id="m119-ack", request_id="m119-ack-request")
        for token in ("synthetic-ai01-token", "synthetic-ai03-token"):
            with self.subTest(token=token), self.assertRaises(PermissionError):
                self.backend.acknowledge(token, "m119-ack")
        acknowledged = self.backend.acknowledge(
            "synthetic-ai02-token", "m119-ack")
        replay = self.backend.acknowledge(
            "synthetic-ai02-token", "m119-ack")
        self.assertEqual(acknowledged.acknowledged_by, replay.acknowledged_by)
        self.assertEqual(self.backend.pending(
            "synthetic-ai02-token", "default", 0, 10), [])

    def test_idempotent_replay_requires_exact_payload_including_message_kind(self):
        first = self.submit(message_id="m119-idem", request_id="m119-idem-request")
        replay = self.submit(message_id="m119-idem", request_id="m119-idem-request")
        self.assertIs(first, replay)
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.submit(message_id="m119-idem", request_id="m119-idem-request",
                        kind="MISSION")

    def test_reusing_request_id_with_changed_body_or_recipient_conflicts(self):
        self.submit(message_id="m119-payload", request_id="m119-payload-request")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.submit(message_id="m119-payload", request_id="m119-payload-request",
                        body="altered")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.submit(message_id="m119-payload", request_id="m119-payload-request",
                        recipients=["AI-01"])

    def test_transport_advertises_only_http_long_poll(self):
        policy = self.backend.transport_capabilities(
            "synthetic-ai01-token", "default")
        self.assertEqual(policy["defaultTransport"], "HTTP_LONG_POLL")
        self.assertTrue(policy["transports"]["httpLongPoll"]["enabled"])
        self.assertFalse(policy["transports"]["webSocket"]["enabled"])
        self.assertFalse(policy["transports"]["serverPush"]["enabled"])

    def test_authentication_errors_never_echo_bearer_credentials(self):
        status, body = self.request("GET", "/v1/me/identity",
                                    "synthetic-invalid-secret")
        self.assertEqual(status, 401)
        self.assertNotIn("synthetic-invalid-secret", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
