import json
import os
import sqlite3
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.operational_runtime import OperationalRuntime
from server.rate_limit import SQLiteSlidingWindowRateLimiter, RateLimitExceeded


class HttpE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B", "token-c": "AI-C"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SQLiteSlidingWindowRateLimiter(self.store)
        MessengerHandler.operational = OperationalRuntime()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.operational = None

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

    def test_readyz_rejects_duplicate_ai_credentials(self):
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ.update({
                "MESSENGER_TOKEN_AI_A": "same-secret",
                "MESSENGER_TOKEN_AI_B": "same-secret",
                "MESSENGER_AI_ID_A": "AI-A",
                "MESSENGER_AI_ID_B": "AI-B",
                "MESSENGER_DB_PATH": self.tmp.name})
            status, data = self.request("GET", "/readyz", "")
            self.assertEqual(status, 503)
            self.assertEqual(data["status"], "not_ready")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


    def test_readyz_rejects_ephemeral_hosted_storage(self):
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B",
                "MESSENGER_DB_PATH", "MESSENGER_STORAGE_MODE"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ.update({
                "MESSENGER_TOKEN_AI_A": "secret-a",
                "MESSENGER_TOKEN_AI_B": "secret-b",
                "MESSENGER_AI_ID_A": "AI-A",
                "MESSENGER_AI_ID_B": "AI-B",
                "MESSENGER_DB_PATH": self.tmp.name,
                "MESSENGER_STORAGE_MODE": "ephemeral"})
            status, data = self.request("GET", "/readyz", "")
            self.assertEqual(status, 503)
            self.assertEqual(data["status"], "not_ready")
            self.assertEqual(data["error"], "runtime_configuration_invalid")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


    def test_readyz_accepts_declared_persistent_root_and_reports_mode(self):
        from pathlib import Path
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B",
                "MESSENGER_DB_PATH", "MESSENGER_STORAGE_MODE",
                "MESSENGER_PERSISTENT_STORAGE_ROOT"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            with tempfile.TemporaryDirectory() as directory:
                db_path = str(Path(directory) / "messenger.sqlite")
                store = SQLiteMessengerStore(db_path)
                store.close()
                os.environ.update({
                    "MESSENGER_TOKEN_AI_A": "secret-a",
                    "MESSENGER_TOKEN_AI_B": "secret-b",
                    "MESSENGER_AI_ID_A": "AI-A",
                    "MESSENGER_AI_ID_B": "AI-B",
                    "MESSENGER_DB_PATH": db_path,
                    "MESSENGER_STORAGE_MODE": "persistent",
                    "MESSENGER_PERSISTENT_STORAGE_ROOT": directory})
                status, data = self.request("GET", "/readyz", "")
                self.assertEqual(status, 200)
                self.assertEqual(data["status"], "ready")
                self.assertEqual(data["storageMode"], "persistent")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


    def test_readyz_rejects_corrupt_database_even_under_persistent_root(self):
        from pathlib import Path
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B",
                "MESSENGER_DB_PATH", "MESSENGER_STORAGE_MODE",
                "MESSENGER_PERSISTENT_STORAGE_ROOT"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            with tempfile.TemporaryDirectory() as directory:
                corrupt = Path(directory) / "corrupt.sqlite"
                corrupt.write_text("not a sqlite database", encoding="utf-8")
                os.environ.update({
                    "MESSENGER_TOKEN_AI_A": "secret-a",
                    "MESSENGER_TOKEN_AI_B": "secret-b",
                    "MESSENGER_AI_ID_A": "AI-A",
                    "MESSENGER_AI_ID_B": "AI-B",
                    "MESSENGER_DB_PATH": str(corrupt),
                    "MESSENGER_STORAGE_MODE": "persistent",
                    "MESSENGER_PERSISTENT_STORAGE_ROOT": directory})
                status, data = self.request("GET", "/readyz", "")
                self.assertEqual(status, 503)
                self.assertEqual(data["error"], "storage_unavailable_or_invalid")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


    def test_readyz_rejects_database_with_wrong_messenger_schema(self):
        from pathlib import Path
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B",
                "MESSENGER_DB_PATH", "MESSENGER_STORAGE_MODE",
                "MESSENGER_PERSISTENT_STORAGE_ROOT"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            with tempfile.TemporaryDirectory() as directory:
                wrong = Path(directory) / "wrong.sqlite"
                with sqlite3.connect(wrong) as connection:
                    connection.execute("CREATE TABLE unrelated (value TEXT)")
                os.environ.update({
                    "MESSENGER_TOKEN_AI_A": "secret-a",
                    "MESSENGER_TOKEN_AI_B": "secret-b",
                    "MESSENGER_AI_ID_A": "AI-A",
                    "MESSENGER_AI_ID_B": "AI-B",
                    "MESSENGER_DB_PATH": str(wrong),
                    "MESSENGER_STORAGE_MODE": "persistent",
                    "MESSENGER_PERSISTENT_STORAGE_ROOT": directory})
                status, data = self.request("GET", "/readyz", "")
                self.assertEqual(status, 503)
                self.assertEqual(data["error"], "storage_unavailable_or_invalid")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

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

        # Simulate a backend process restart before recipient AI-B polls.
        self.backend.close()
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend

        status, pending = self.request(
            "GET", "/v1/conversations/private-ai-a-b/messages?after=0&limit=100", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(pending["principalAiId"], "AI-B")
        self.assertEqual(len(pending["messages"]), 1)
        self.assertEqual(pending["messages"][0]["body"], "mensagem de AI-A para AI-B")

        status, ack = self.request("POST", "/v1/messages/m-private-flow/ack", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(ack["state"], "ACKNOWLEDGED")

        # Acknowledgement state must also survive a backend process restart.
        self.backend.close()
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend

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


    def test_http_rate_limit_is_persisted_and_shared_by_handler(self):
        MessengerHandler.rate_limiter = SQLiteSlidingWindowRateLimiter(
            self.store, max_events=1, window_seconds=60, clock=lambda: 100.0)
        status, created = self.request(
            "POST", "/v1/conversations/room/invitations", "token-a",
            {"targetAiId": "AI-C"})
        self.assertEqual(status, 201)
        status, limited = self.request(
            "POST", "/v1/invitations/accept", "token-a",
            {"token": "x" * 50})
        self.assertEqual(status, 429)
        self.assertEqual(limited["error"], "rate_limit_exceeded")

    def test_http_invitation_create_accept_is_target_bound_and_single_use(self):
        status, created = self.request(
            "POST", "/v1/conversations/room/invitations", "token-a",
            {"targetAiId": "AI-C"})
        self.assertEqual(status, 201)
        invitation = created["invitation"]
        self.assertNotIn("token", str(self.auth.audit_log.events()))
        stored = self.store._connection.execute(
            "SELECT token_hash, status FROM invitations WHERE invitation_id=?",
            (invitation["invitationId"],)).fetchone()
        self.assertEqual(len(stored["token_hash"]), 64)
        self.assertNotEqual(stored["token_hash"], invitation["token"])
        self.assertEqual(stored["status"], "PENDING")

        status, wrong_target = self.request(
            "POST", "/v1/invitations/accept", "token-b",
            {"token": invitation["token"]})
        self.assertEqual(status, 400)
        self.assertEqual(wrong_target["error"], "invitation_unavailable")

        status, accepted = self.request(
            "POST", "/v1/invitations/accept", "token-c",
            {"token": invitation["token"]})
        self.assertEqual(status, 200)
        self.assertEqual(accepted["conversation"]["memberCount"], 3)

        status, replay = self.request(
            "POST", "/v1/invitations/accept", "token-c",
            {"token": invitation["token"]})
        self.assertEqual(status, 400)
        self.assertEqual(replay["error"], "invitation_unavailable")

    def test_http_invitation_cannot_expand_private_conversation(self):
        status, created = self.request(
            "POST", "/v1/conversations", "token-a",
            {"conversationId": "private-room", "memberAiIds": ["AI-A", "AI-B"], "kind": "PRIVATE"})
        self.assertEqual(status, 201)
        status, denied = self.request(
            "POST", "/v1/conversations/private-room/invitations", "token-a",
            {"targetAiId": "AI-C"})
        self.assertEqual(status, 400)
        self.assertEqual(denied["error"], "invitation_unavailable")

    def test_http_invitation_revoke_requires_creator(self):
        status, created = self.request(
            "POST", "/v1/conversations/room/invitations", "token-a",
            {"targetAiId": "AI-C"})
        self.assertEqual(status, 201)
        invitation_id = created["invitation"]["invitationId"]

        status, denied = self.request(
            "POST", f"/v1/invitations/{invitation_id}/revoke", "token-b")
        self.assertEqual(status, 400)
        self.assertEqual(denied["error"], "invitation_unavailable")

        status, revoked = self.request(
            "POST", f"/v1/invitations/{invitation_id}/revoke", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual(revoked["state"], "REVOKED")

        status, accepted = self.request(
            "POST", "/v1/invitations/accept", "token-c",
            {"token": created["invitation"]["token"]})
        self.assertEqual(status, 400)
        self.assertEqual(accepted["error"], "invitation_unavailable")


if __name__ == "__main__":
    unittest.main()
