"""Mission 122: local-only HTTP Long Poll delivery, ACK, replay, and restart proof.

All requests target an ephemeral 127.0.0.1 listener and synthetic credentials.
No Render, external network, physical device, or real AI credential is used.
"""
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore


class Mission122LongPollDeliveryProofTest(unittest.TestCase):
    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.db.close()
        self.tokens = {
            "synthetic-token-ai01": "AI-01",
            "synthetic-token-ai02": "AI-02",
            "synthetic-token-ai03": "AI-03",
        }
        self._start_runtime()

    def _start_runtime(self):
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.db.name)
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _stop_runtime(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()

    def tearDown(self):
        self._stop_runtime()
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        import os
        os.unlink(self.db.name)

    def request(self, method, path, token, payload=None, timeout=5):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=timeout)
        headers = {"Authorization": "Bearer " + token}
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def send(self, body="hello AI-02", message_id="m122-message-001",
             request_id="m122-request-001"):
        return self.request("POST", "/v1/messages", "synthetic-token-ai01", {
            "messageId": message_id, "conversationId": "default",
            "recipientAiIds": ["AI-02"], "body": body,
            "clientRequestId": request_id,
        })

    def poll(self, token="synthetic-token-ai02", after=0, timeout=0):
        return self.request(
            "GET",
            f"/v1/conversations/default/messages/wait?after={after}&limit=10&timeout={timeout}",
            token, timeout=max(5, timeout + 2))

    def test_ai_credentials_resolve_to_distinct_http_identities(self):
        status_a, identity_a = self.request(
            "GET", "/v1/me/identity", "synthetic-token-ai01")
        status_b, identity_b = self.request(
            "GET", "/v1/me/identity", "synthetic-token-ai02")
        self.assertEqual((status_a, status_b), (200, 200))
        self.assertEqual(identity_a["identity"]["aiId"], "AI-01")
        self.assertEqual(identity_b["identity"]["aiId"], "AI-02")

    def test_long_poll_receives_message_after_sender_posts(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            waiting = pool.submit(self.poll, "synthetic-token-ai02", 0, 3)
            time.sleep(0.15)
            status, queued = self.send()
            self.assertEqual(status, 200)
            self.assertEqual(queued["state"], "QUEUED")
            poll_status, received = waiting.result(timeout=5)
        self.assertEqual(poll_status, 200)
        self.assertEqual(len(received["messages"]), 1)
        self.assertEqual(received["messages"][0]["messageId"], queued["messageId"])
        self.assertEqual(received["messages"][0]["senderAiId"], "AI-01")
        self.assertEqual(received["messages"][0]["body"], "hello AI-02")

    def test_sender_cannot_ack_its_own_outbound_message(self):
        self.send()
        status, result = self.request(
            "POST", "/v1/messages/m122-message-001/ack", "synthetic-token-ai01", {})
        self.assertEqual(status, 403)
        self.assertEqual(result["error"], "forbidden")
        self.assertEqual(len(self.poll()[1]["messages"]), 1)

    def test_only_recipient_can_poll_the_room(self):
        status, result = self.poll("synthetic-token-ai03")
        self.assertEqual(status, 403)
        self.assertEqual(result["error"], "forbidden")

    def test_recipient_ack_is_idempotent_and_removes_pending_delivery(self):
        self.send()
        first_status, first = self.request(
            "POST", "/v1/messages/m122-message-001/ack", "synthetic-token-ai02", {})
        second_status, second = self.request(
            "POST", "/v1/messages/m122-message-001/ack", "synthetic-token-ai02", {})
        self.assertEqual((first_status, second_status), (200, 200))
        self.assertEqual(first["state"], "ACKNOWLEDGED")
        self.assertEqual(second["state"], "ACKNOWLEDGED")
        poll_status, pending = self.poll()
        self.assertEqual(poll_status, 200)
        self.assertEqual(pending["messages"], [])

    def test_exact_http_retry_does_not_create_a_second_sequence(self):
        first_status, first = self.send()
        retry_status, retry = self.send()
        self.assertEqual((first_status, retry_status), (200, 200))
        self.assertEqual(first["messageId"], retry["messageId"])
        self.assertEqual(first["sequence"], retry["sequence"])
        self.assertEqual(len(self.poll()[1]["messages"]), 1)

    def test_changed_payload_with_same_request_id_is_rejected(self):
        self.send()
        status, result = self.send(body="changed payload")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_request")
        self.assertEqual(len(self.poll()[1]["messages"]), 1)

    def test_acknowledgement_survives_server_backend_restart(self):
        self.send()
        ack_status, ack = self.request(
            "POST", "/v1/messages/m122-message-001/ack", "synthetic-token-ai02", {})
        self.assertEqual(ack_status, 200)
        self._stop_runtime()
        self._start_runtime()
        poll_status, pending = self.poll()
        self.assertEqual(poll_status, 200)
        self.assertEqual(pending["messages"], [])
        history_status, history = self.request(
            "GET", "/v1/conversations/default/history?before=0&limit=10",
            "synthetic-token-ai02")
        self.assertEqual(history_status, 200)
        self.assertEqual([item["messageId"] for item in history["messages"]],
                         ["m122-message-001"])


if __name__ == "__main__":
    unittest.main()
