import unittest

from server.audit import AuditLog
from server.auth import Authenticator
from server.messenger_backend import MessengerBackend


class Mission14SecurityTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, authenticator=self.auth)

    def tearDown(self):
        self.backend.close()

    def test_sender_identity_spoof_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "sender_identity_mismatch"):
            self.backend.assert_authenticated_sender("token-a", "AI-B")

    def test_recipient_outside_conversation_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "recipient_authorization_denied"):
            self.backend.submit("token-a", "m1", "room", ["AI-C"], "x", "req-1")

    def test_idempotent_replay_returns_original_message(self):
        first = self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "req-1")
        replay = self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "req-1")
        self.assertEqual(first.message_id, replay.message_id)
        self.assertEqual(first.sequence, replay.sequence)

    def test_idempotency_conflict_is_rejected(self):
        self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "req-1")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.backend.submit("token-a", "m2", "room", ["AI-B"], "different", "req-1")

    def test_audit_event_ids_and_secret_filtering(self):
        log = AuditLog()
        event = log.record("AUTHENTICATED", "credential", ai_id="AI-A", metadata={"token": "secret", "request_id": "r1"})
        self.assertTrue(event.event_id)
        self.assertTrue(event.correlation_id)
        self.assertNotIn("token", event.metadata)
        self.assertEqual(event.metadata["request_id"], "r1")


if __name__ == "__main__":
    unittest.main()
