import json
import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore
from server.operational_runtime import OperationalRuntime


class HttpE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B", "token-c": "AI-C"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        from server.rate_limit import SlidingWindowRateLimiter
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.authenticator = self.auth
        from server.voice_room_control import VoiceRoomControl
        MessengerHandler.voice_control = VoiceRoomControl({"AI-A"}, store=self.store)
        MessengerHandler.operational = OperationalRuntime()
        self.audio_dir = tempfile.TemporaryDirectory()
        MessengerHandler.audio_store = AudioBlobStore(self.audio_dir.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        self.audio_dir.cleanup()

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

    def request_bytes(self, method, path, token, data=b"", content_type="audio/ogg"):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Authorization": "Bearer " + token, "Content-Type": content_type}
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        payload = response.read()
        headers_out = dict(response.getheaders())
        conn.close()
        return response.status, payload, headers_out

    def test_admin_can_mute_and_unmute_room_participant_over_http(self):
        status, data = self.request("POST", "/v1/conversations/room/voice/mute",
                                    "token-a", {"targetAiId": "AI-B"})
        self.assertEqual(status, 200)
        self.assertTrue(data["voiceControl"]["muted"])
        self.assertIsInstance(data["voiceControl"]["expiresAt"], (int, float))
        from server.voice_room_control import VoiceRoomControl
        MessengerHandler.voice_control = VoiceRoomControl({"AI-A"}, store=self.store)
        self.assertTrue(MessengerHandler.voice_control.is_muted("room", "AI-B"))
        status, data = self.request("POST", "/v1/conversations/room/voice/unmute",
                                    "token-a", {"targetAiId": "AI-B"})
        self.assertEqual(status, 200)
        self.assertFalse(data["voiceControl"]["muted"])
        events = [event.event_type for event in self.auth.audit_log.events()]
        self.assertIn("VOICE_PARTICIPANT_MUTED", events)
        self.assertIn("VOICE_PARTICIPANT_UNMUTED", events)

    def test_room_member_can_read_persisted_voice_mute_state(self):
        status, _ = self.request("POST", "/v1/conversations/room/voice/mute",
                                 "token-a", {"targetAiId": "AI-B"})
        self.assertEqual(status, 200)
        status, data = self.request("GET", "/v1/conversations/room/voice/status",
                                    "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(data["conversationId"], "room")
        self.assertEqual(data["mutedAiIds"], ["AI-B"])
        events = [event.event_type for event in self.auth.audit_log.events()]
        self.assertIn("VOICE_ROOM_STATE_READ", events)

    def test_voice_status_rejects_non_member_and_missing_authentication(self):
        status, data = self.request("GET", "/v1/conversations/unknown/voice/status",
                                    "token-b")
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")
        status, data = self.request("GET", "/v1/conversations/room/voice/status", "")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

    def test_http_mute_rejects_unbounded_duration(self):
        status, data = self.request("POST", "/v1/conversations/room/voice/mute",
                                    "token-a", {"targetAiId": "AI-B",
                                                "durationSeconds": 3601})
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_voice_control_request")

    def test_non_admin_cannot_mute_participant_over_http(self):
        status, data = self.request("POST", "/v1/conversations/room/voice/mute",
                                    "token-b", {"targetAiId": "AI-A"})
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")

    def test_voice_mute_rejects_target_outside_room(self):
        status, data = self.request("POST", "/v1/conversations/room/voice/mute",
                                    "token-a", {"targetAiId": "AI-UNKNOWN"})
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")

    def test_authenticated_audio_upload_and_download(self):
        status, _, _ = self.request_bytes("POST", "/v1/messages/audio-http/audio", "token-a", b"OggS" + b"x" * 20)
        self.assertEqual(status, 404)
        self.request("POST", "/v1/messages", "token-a", {
            "messageId": "audio-http", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "voice", "clientRequestId": "audio-http-req"})
        status, body, _ = self.request_bytes("POST", "/v1/messages/audio-http/audio", "token-a", b"OggS" + b"x" * 20)
        self.assertEqual(status, 201)
        metadata = json.loads(body.decode("utf-8"))
        object_id = metadata["attachment"]["objectId"]
        self.assertEqual(metadata["attachment"]["contentType"], "audio/ogg")

        status, downloaded, headers = self.request_bytes("GET", f"/v1/messages/audio-http/audio/{object_id}", "token-b", b"", "application/octet-stream")
        self.assertEqual(status, 200)
        self.assertEqual(downloaded, b"OggS" + b"x" * 20)
        self.assertEqual(headers["Content-Type"], "application/octet-stream")

    def test_audio_upload_rejects_spoofed_sender_and_invalid_audio(self):
        self.request("POST", "/v1/messages", "token-a", {
            "messageId": "audio-guard", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "voice", "clientRequestId": "audio-guard-req"})
        status, _, _ = self.request_bytes("POST", "/v1/messages/audio-guard/audio", "token-b", b"OggS" + b"x" * 20)
        self.assertEqual(status, 403)
        status, body, _ = self.request_bytes("POST", "/v1/messages/audio-guard/audio", "token-a", b"not-audio")
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body.decode("utf-8"))["error"], "invalid_audio")

    def test_audio_download_is_member_only(self):
        self.request("POST", "/v1/messages", "token-a", {
            "messageId": "audio-member", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "voice", "clientRequestId": "audio-member-req"})
        status, body, _ = self.request_bytes("POST", "/v1/messages/audio-member/audio", "token-a", b"OggS" + b"x" * 20)
        object_id = json.loads(body.decode("utf-8"))["attachment"]["objectId"]
        status, _, _ = self.request_bytes("GET", f"/v1/messages/audio-member/audio/{object_id}", "bad-token", b"", "application/octet-stream")
        self.assertEqual(status, 401)

    def test_legacy_phone_number_endpoint_is_disabled(self):
        status, data = self.request("GET", "/v1/me/phone", "token-a")
        self.assertEqual(status, 404)
        self.assertEqual(data["error"], "not_found")

    def test_authenticated_internal_identity_has_no_phone_number(self):
        status, data = self.request("GET", "/v1/me/identity", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual(data["identity"]["aiId"], "AI-A")
        self.assertNotIn("displayNumber", data["identity"])
        self.assertNotIn("serial", data["identity"])

    def test_internal_identity_rejects_missing_authentication(self):
        status, data = self.request("GET", "/v1/me/identity", "")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

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

    def test_http_audio_attachment_listing_is_member_only(self):
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-audio-list", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "audio list",
            "clientRequestId": "req-audio-list"})
        self.assertEqual(status, 200)
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        body = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"
        conn.request("POST", "/v1/messages/m-audio-list/audio", body=body, headers={
            "Authorization":"Bearer token-a","Content-Type":"audio/mp4","Content-Length":str(len(body))})
        response=conn.getresponse(); response.read(); conn.close()
        self.assertEqual(response.status, 201)
        status, data = self.request("GET", "/v1/messages/m-audio-list/audio", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["attachments"]), 1)
        status, data = self.request("GET", "/v1/messages/m-audio-list/audio", "token-x")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

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


    def test_polling_endpoint_is_rate_limited_per_authenticated_ai(self):
        from server.rate_limit import SlidingWindowRateLimiter
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        first_status, _ = self.request("GET", "/v1/conversations/room/messages", "token-b")
        second_status, data = self.request("GET", "/v1/conversations/room/messages", "token-b")
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 429)
        self.assertEqual(data["error"], "rate_limit_exceeded")

    def test_acknowledgement_endpoint_is_rate_limited_per_authenticated_ai(self):
        from server.rate_limit import SlidingWindowRateLimiter
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-rate-limit-ack", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "rate limit ack",
            "clientRequestId": "req-rate-limit-ack"})
        self.assertEqual(status, 200)
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        first_status, _ = self.request("POST", "/v1/messages/m-rate-limit-ack/ack", "token-b")
        second_status, data = self.request("POST", "/v1/messages/m-rate-limit-ack/ack", "token-b")
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 429)
        self.assertEqual(data["error"], "rate_limit_exceeded")

    def test_http_rejects_non_string_message_body_without_server_error(self):
        status, data = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-invalid-body", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": ["not", "text"],
            "clientRequestId": "req-invalid-body"})
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_blank_message_body(self):
        status, data = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-blank-body", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "   ",
            "clientRequestId": "req-blank-body"})
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_non_list_recipients(self):
        status, data = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-invalid-recipients", "conversationId": "room",
            "recipientAiIds": "AI-B", "body": "body",
            "clientRequestId": "req-invalid-recipients"})
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_ack_accepts_query_string_without_corrupting_message_id(self):
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-ack-query", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "ack query",
            "clientRequestId": "req-ack-query"})
        self.assertEqual(status, 200)
        status, data = self.request("POST", "/v1/messages/m-ack-query/ack?source=poll", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(data["messageId"], "m-ack-query")

    def test_http_rejects_invalid_utf8_json_with_400(self):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/messages", body=b"\xff\xfe", headers={
            "Authorization": "Bearer token-a",
            "Content-Type": "application/json",
            "Content-Length": "2"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_non_json_content_type(self):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/messages", body=b"{}", headers={
            "Authorization": "Bearer token-a", "Content-Type": "text/plain"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_malformed_json(self):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/messages", body=b"{broken", headers={
            "Authorization": "Bearer token-a", "Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_oversized_request_body_before_reading_payload(self):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.putrequest("POST", "/v1/messages")
        conn.putheader("Authorization", "Bearer token-a")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", "10001")
        conn.endheaders()
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_invalid_poll_cursors(self):
        for query in ("after=-1", "limit=101", "after=not-a-number"):
            with self.subTest(query=query):
                status, data = self.request(
                    "GET", "/v1/conversations/room/messages?" + query, "token-b")
                self.assertEqual(status, 400)
                self.assertEqual(data["error"], "invalid_cursor")

    def test_http_concurrent_duplicate_submissions_create_one_message(self):
        payload = {
            "messageId": "m-http-concurrent",
            "conversationId": "room",
            "recipientAiIds": ["AI-B"],
            "body": "one logical concurrent HTTP message",
            "clientRequestId": "req-http-concurrent",
        }
        def submit(_):
            return self.request("POST", "/v1/messages", "token-a", payload)
        with ThreadPoolExecutor(max_workers=10) as pool:
            responses = list(pool.map(submit, range(10)))
        self.assertEqual({status for status, _ in responses}, {200})
        self.assertEqual(
            {data["messageId"] for _, data in responses}, {"m-http-concurrent"})
        status, pending = self.request(
            "GET", "/v1/conversations/room/messages", "token-b")
        self.assertEqual(status, 200)
        matches = [m for m in pending["messages"]
                   if m["messageId"] == "m-http-concurrent"]
        self.assertEqual(len(matches), 1)

    def test_http_rejects_duplicate_json_keys(self):
        body = (b'{"messageId":"first","messageId":"second",'
                b'"conversationId":"room","recipientAiIds":["AI-B"],'
                b'"body":"ambiguous","clientRequestId":"req-duplicate-key"}')
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/messages", body=body, headers={
            "Authorization": "Bearer token-a",
            "Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_http_rejects_nonstandard_json_nan(self):
        body = (b'{"messageId":"m-nan","conversationId":"room",'
                b'"recipientAiIds":["AI-B"],"body":NaN,'
                b'"clientRequestId":"req-nan"}')
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/messages", body=body, headers={
            "Authorization": "Bearer token-a",
            "Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["error"], "invalid_request")

    def test_authenticated_conversation_list_returns_only_member_rooms(self):
        self.backend.create_conversation(
            "token-a", "private-room", ["AI-A", "AI-B"], "PRIVATE")
        status, data = self.request("GET", "/v1/conversations", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual(
            [item["conversationId"] for item in data["conversations"]],
            ["private-room", "room"])
        self.assertEqual(data["conversations"][0]["kind"], "PRIVATE")
        status, outsider = self.request("GET", "/v1/conversations", "token-c")
        self.assertEqual(status, 200)
        self.assertEqual(outsider["conversations"], [])
        self.assertEqual(outsider["principalAiId"], "AI-C")
        events = [event.event_type for event in self.auth.audit_log.events()]
        self.assertIn("CONVERSATIONS_LISTED", events)

    def test_conversation_list_requires_authentication_and_valid_query(self):
        status, data = self.request("GET", "/v1/conversations", "")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")
        for path in ("/v1/conversations?limit=0",
                     "/v1/conversations?limit=101",
                     "/v1/conversations?limit=2&limit=3",
                     "/v1/conversations?unknown=1"):
            with self.subTest(path=path):
                status, data = self.request("GET", path, "token-a")
                self.assertEqual(status, 400)
                self.assertEqual(data["error"], "invalid_conversation_query")

    def test_browser_root_serves_chat_first_rooms_home(self):
        for path in ("/", "/rooms"):
            with self.subTest(path=path):
                connection = HTTPConnection(
                    "127.0.0.1", self.server.server_port, timeout=3)
                connection.request("GET", path)
                response = connection.getresponse()
                body = response.read().decode("utf-8")
                headers = dict(response.getheaders())
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertIn("text/html", headers["Content-Type"])
                self.assertIn("AI Bridge", body)
                self.assertIn("Central de Salas", body)
                self.assertNotIn("href=\"http", body)

    def test_rooms_flow_lists_reads_and_acknowledges_real_messages(self):
        status, submitted = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "rooms-flow-message",
            "conversationId": "room",
            "recipientAiIds": ["AI-B"],
            "body": "Mensagem de teste da sala",
            "clientRequestId": "rooms-flow-request"})
        self.assertEqual(status, 200)
        status, listing = self.request("GET", "/v1/conversations", "token-b")
        self.assertEqual(status, 200)
        self.assertIn("room", [item["conversationId"]
                               for item in listing["conversations"]])
        status, inbox = self.request(
            "GET", "/v1/conversations/room/messages?after=0&limit=50", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(inbox["messages"][0]["messageId"],
                         "rooms-flow-message")
        self.assertEqual(inbox["messages"][0]["body"],
                         "Mensagem de teste da sala")
        status, ack = self.request(
            "POST", "/v1/messages/rooms-flow-message/ack", "token-b", {})
        self.assertEqual(status, 200)
        self.assertEqual(ack["state"], "ACKNOWLEDGED")
        status, inbox_after_ack = self.request(
            "GET", "/v1/conversations/room/messages?after=0&limit=50", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(inbox_after_ack["messages"], [])


    def test_web_invite_request_and_admin_approval_over_http(self):
        status, created = self.request("POST", "/v1/conversations", "token-a", {
            "conversationId": "web-invite-room",
            "memberAiIds": ["AI-A", "AI-B"], "kind": "GROUP"})
        self.assertEqual(status, 201)
        status, invite_data = self.request(
            "POST", "/v1/conversations/web-invite-room/invites", "token-a",
            {"expiresInSeconds": 600, "maxUses": 2})
        self.assertEqual(status, 201)
        invite = invite_data["invite"]
        self.assertTrue(invite["token"])
        status, public = self.request(
            "GET", "/v1/invites/" + invite["inviteId"], "")
        self.assertEqual(status, 200)
        self.assertEqual(public["invite"]["status"], "ACTIVE")
        self.assertNotIn("token", public["invite"])

        status, request_data = self.request(
            "POST", "/v1/invites/redeem", "token-c", {"token": invite["token"]})
        self.assertEqual(status, 202)
        request_id = request_data["request"]["requestId"]
        status, listing = self.request(
            "GET", "/v1/conversations/web-invite-room/join-requests", "token-b")
        self.assertEqual(status, 403)
        status, listing = self.request(
            "GET", "/v1/conversations/web-invite-room/join-requests", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual(listing["requests"][0]["ai_id"], "AI-C")
        status, decision = self.request(
            "POST",
            "/v1/conversations/web-invite-room/join-requests/" + request_id + "/decision",
            "token-a", {"decision": "APPROVE"})
        self.assertEqual(status, 200)
        self.assertEqual(decision["request"]["status"], "APPROVED")
        status, rooms = self.request("GET", "/v1/conversations", "token-c")
        self.assertEqual(status, 200)
        self.assertIn("web-invite-room",
                      [room["conversationId"] for room in rooms["conversations"]])

    def test_web_invite_requires_admin_and_revocation_blocks_redeem(self):
        self.request("POST", "/v1/conversations", "token-a", {
            "conversationId": "web-invite-revoke",
            "memberAiIds": ["AI-A", "AI-B"], "kind": "GROUP"})
        status, forbidden = self.request(
            "POST", "/v1/conversations/web-invite-revoke/invites", "token-b", {})
        self.assertEqual(status, 403)
        status, created = self.request(
            "POST", "/v1/conversations/web-invite-revoke/invites", "token-a", {})
        self.assertEqual(status, 201)
        invite = created["invite"]
        status, revoked = self.request(
            "DELETE", "/v1/conversations/web-invite-revoke/invites/" +
            invite["inviteId"], "token-a")
        self.assertEqual(status, 200)
        status, redeem = self.request(
            "POST", "/v1/invites/redeem", "token-c", {"token": invite["token"]})
        self.assertEqual(status, 400)
        self.assertEqual(redeem["error"], "invite_unavailable")

    def test_web_invite_rejects_missing_authentication_and_invalid_decision(self):
        self.request("POST", "/v1/conversations", "token-a", {
            "conversationId": "web-invite-invalid",
            "memberAiIds": ["AI-A", "AI-B"], "kind": "GROUP"})
        status, data = self.request(
            "POST", "/v1/conversations/web-invite-invalid/invites", "", {})
        self.assertEqual(status, 401)
        status, created = self.request(
            "POST", "/v1/conversations/web-invite-invalid/invites", "token-a", {})
        self.assertEqual(status, 201)
        invite = created["invite"]
        status, request_data = self.request(
            "POST", "/v1/invites/redeem", "token-c", {"token": invite["token"]})
        self.assertEqual(status, 202)
        request_id = request_data["request"]["requestId"]
        status, invalid = self.request(
            "POST",
            "/v1/conversations/web-invite-invalid/join-requests/" + request_id + "/decision",
            "token-a", {"decision": "MAYBE"})
        self.assertEqual(status, 400)


    def test_invite_page_is_served_without_referrer_and_cache(self):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("GET", "/invite")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        headers = dict(response.getheaders())
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn("Solicitar entrada", body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")

if __name__ == "__main__":
    unittest.main()
