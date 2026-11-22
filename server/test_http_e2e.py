import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class HttpE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.backend.close()

    def request(self, method, path, token, payload=None, correlation_id=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        body = None
        headers = {"Authorization": "Bearer " + token}
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, data

    def test_two_principal_http_flow(self):
        status, sent = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-http-1", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "hello over local HTTP",
            "clientRequestId": "req-http-1"})
        self.assertEqual(status, 200); self.assertEqual(sent["senderAiId"], "AI-A")

        status, pending = self.request("GET", "/v1/conversations/room/messages", "token-b")
        self.assertEqual(status, 200); self.assertEqual(pending["principalAiId"], "AI-B")
        self.assertEqual(pending["messages"][0]["messageId"], "m-http-1")

        status, ack = self.request("POST", "/v1/messages/m-http-1/ack", "token-b")
        self.assertEqual(status, 200); self.assertEqual(ack["state"], "ACKNOWLEDGED")

    def test_create_private_conversation_send_receive_and_ack(self):
        status, created = self.request("POST", "/v1/conversations", "token-a", {
            "conversationId": "private-ai-a-b",
            "memberAiIds": ["AI-A", "AI-B"],
            "kind": "PRIVATE"})
        self.assertEqual(status, 201)
        self.assertEqual(created["conversation"]["memberCount"], 2)
        self.assertEqual(created["conversation"]["kind"], "PRIVATE")

        status, sent = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-private-flow", "conversationId": "private-ai-a-b",
            "recipientAiIds": ["AI-B"], "body": "mensagem de AI-A para AI-B",
            "clientRequestId": "req-private-flow"})
        self.assertEqual(status, 200)
        self.assertEqual(sent["state"], "QUEUED")
        self.assertEqual(sent["senderAiId"], "AI-A")

        status, pending = self.request(
            "GET", "/v1/conversations/private-ai-a-b/messages?after=0&limit=100", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(pending["principalAiId"], "AI-B")
        self.assertEqual(len(pending["messages"]), 1)
        self.assertEqual(pending["messages"][0]["body"], "mensagem de AI-A para AI-B")

        status, ack = self.request("POST", "/v1/messages/m-private-flow/ack", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(ack["state"], "ACKNOWLEDGED")

        status, pending_after_ack = self.request(
            "GET", "/v1/conversations/private-ai-a-b/messages?after=0&limit=100", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(pending_after_ack["messages"], [])

    def test_http_retry_is_idempotent_for_same_ai_request(self):
        payload = {
            "messageId": "m-idempotent-http", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "retry-safe",
            "clientRequestId": "req-idempotent-http"}
        first_status, first = self.request("POST", "/v1/messages", "token-a", payload)
        retry_status, retry = self.request("POST", "/v1/messages", "token-a", payload)
        self.assertEqual(first_status, 200)
        self.assertEqual(retry_status, 200)
        self.assertEqual(first["messageId"], retry["messageId"])
        self.assertEqual(first["sequence"], retry["sequence"])

        status, pending = self.request("GET", "/v1/conversations/room/messages", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual([m["messageId"] for m in pending["messages"]], ["m-idempotent-http"])

    def test_http_idempotency_conflict_is_rejected(self):
        base = {
            "messageId": "m-idempotency-conflict", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "first body",
            "clientRequestId": "req-idempotency-conflict"}
        status, _ = self.request("POST", "/v1/messages", "token-a", base)
        self.assertEqual(status, 200)
        changed = dict(base)
        changed["body"] = "different body"
        status, data = self.request("POST", "/v1/messages", "token-a", changed)
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_ack_is_recipient_only_and_repeatable(self):
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-ack-guard", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "ack guard",
            "clientRequestId": "req-ack-guard"})
        self.assertEqual(status, 200)

        status, data = self.request("POST", "/v1/messages/m-ack-guard/ack", "token-a")
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")

        status, first = self.request("POST", "/v1/messages/m-ack-guard/ack", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(first["state"], "ACKNOWLEDGED")
        status, second = self.request("POST", "/v1/messages/m-ack-guard/ack", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(second["state"], "ACKNOWLEDGED")

    def test_http_private_conversation_rejects_unauthorized_and_invalid_members(self):
        status, data = self.request("POST", "/v1/conversations", "bad-token", {
            "conversationId": "private-unauth",
            "memberAiIds": ["AI-A", "AI-B"], "kind": "PRIVATE"})
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

        status, data = self.request("POST", "/v1/conversations", "token-a", {
            "conversationId": "private-invalid",
            "memberAiIds": ["AI-A", "AI-B"], "kind": "UNKNOWN"})
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_conversation")

    def test_old_credential_is_rejected_after_rotation(self):
        self.auth.rotate("token-a", "token-a-2")
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-http-2", "conversationId": "room", "recipientAiIds": ["AI-B"],
            "body": "must fail", "clientRequestId": "req-http-2"})
        self.assertEqual(status, 401)

    def test_http_sender_spoof_and_error_sanitization(self):
        status, data = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-spoof", "conversationId": "room", "recipientAiIds": ["AI-B"],
            "senderAiId": "AI-B", "body": "spoof", "clientRequestId": "req-spoof"})
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")

        status, data = self.request("GET", "/v1/conversations/room/messages", "bad-token")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

    def test_http_correlation_id_is_returned_and_audited(self):
        status, data = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-corr", "conversationId": "room", "recipientAiIds": ["AI-B"],
            "body": "correlated", "clientRequestId": "req-corr"}, correlation_id="corr-15")
        self.assertEqual(status, 200)
        self.assertEqual(data["correlationId"], "corr-15")
        events = self.auth.audit_log.events()
        self.assertTrue(any(e.correlation_id == "corr-15" and e.event_type == "MESSAGE_SUBMITTED" for e in events))


if __name__ == "__main__":
    unittest.main()
